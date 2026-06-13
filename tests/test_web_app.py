import asyncio
import base64
import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import openai
import requests
from PIL import Image
from fastapi import HTTPException
from fastapi.testclient import TestClient

(Path(__file__).resolve().parents[1] / "engine" / "web" / "static" / "js").mkdir(parents=True, exist_ok=True)

import engine.api.app as web_app_module
import engine.services.npc_turn_service as npc_turn_service_module
from engine.config import config
from engine.storage import storage
from engine.storage.models import Message


def _make_test_png(path: Path, width: int = 4, height: int = 4) -> Path:
    img = Image.new("RGB", (width, height), color=(80, 120, 160))
    img.save(path, format="PNG")
    return path


def _test_png_data_url(width: int = 4, height: int = 4) -> str:
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(80, 120, 160)).save(buffer, format="PNG")
    payload = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{payload}"


class FakeSessionView:
    saved_calls: list[tuple[str | None, str | None]] = []
    npc_id = "vika"
    scene_id = "office"

    @classmethod
    def save(cls, npc_id: str | None = None, scene_id: str | None = None):
        cls.saved_calls.append((npc_id, scene_id))
        if npc_id is not None:
            cls.npc_id = npc_id
        if scene_id is not None:
            cls.scene_id = scene_id
        return SimpleNamespace(npc_id=cls.npc_id, scene_id=cls.scene_id)


def _write_session(tmp_path: Path, npc_id: str, scene_id: str) -> None:
    FakeSessionView.npc_id = npc_id
    FakeSessionView.scene_id = scene_id
    (tmp_path / "session.yaml").write_text(
        f"npc_id: {npc_id}\nscene_id: {scene_id}\n",
        encoding="utf-8",
    )


class FakeNpcTurnService:
    def __init__(self) -> None:
        self.user_message = None

    def build_chat_messages(self, player_input: str):
        user_message = {"role": "user", "content": player_input}
        self.user_message = user_message
        return [{"role": "system", "content": "stub"}, user_message]

    def finalize_turn(self, player_input: str, assistant_reply: str) -> None:
        user_msg = Message(
            id="m-user",
            timestamp_utc="2026-03-22T10:02:00+00:00",
            role="user",
            content=player_input.strip(),
        )
        assistant_msg = Message(
            id="m-assistant",
            timestamp_utc="2026-03-22T10:03:00+00:00",
            role="assistant",
            content=assistant_reply.strip(),
        )
        web_app_module.storage.npc.stm.append(user_msg)
        web_app_module.storage.npc.stm.append(assistant_msg)


def _patch_scheduler(monkeypatch, scheduler_factory) -> None:
    monkeypatch.setattr(web_app_module.chat, "get_scheduler", scheduler_factory)
    monkeypatch.setattr(web_app_module.session, "get_scheduler", scheduler_factory, raising=False)
    monkeypatch.setattr(web_app_module.scene, "get_scheduler", scheduler_factory, raising=False)
    monkeypatch.setattr(web_app_module.npc, "get_scheduler", scheduler_factory)
    monkeypatch.setattr("engine.tools.scheduler.get_scheduler", scheduler_factory)


def _patch_streaming_response(monkeypatch, response_cls) -> None:
    monkeypatch.setattr(
        web_app_module.chat,
        "StreamingResponse",
        lambda content, media_type: response_cls(content, media_type),
    )


def _patch_image_service(monkeypatch, service_cls) -> None:
    monkeypatch.setattr(web_app_module.session, "ImageService", service_cls)


def _patch_npc_turn_service(monkeypatch, service_cls) -> None:
    monkeypatch.setattr(web_app_module.chat, "NpcTurnService", service_cls)


def _setup_web_app(
    tmp_path,
    monkeypatch,
    *,
    web_debug: bool = False,
) -> None:
    npcs_dir = tmp_path / "npcs"
    avatars_dir = tmp_path / "avatars"
    scenes_dir = tmp_path / "scenes"
    data_npcs_dir = tmp_path / ".data" / "npcs"
    overrides_npcs_dir = tmp_path / ".overrides" / "npcs"
    overrides_avatars_dir = tmp_path / ".overrides" / "avatars"
    overrides_scenes_dir = tmp_path / ".overrides" / "scenes"
    overrides_npcs_dir.mkdir(parents=True, exist_ok=True)
    overrides_avatars_dir.mkdir(parents=True, exist_ok=True)
    overrides_scenes_dir.mkdir(parents=True, exist_ok=True)

    for npc_id, label in (("vika", "Vika"), ("mira", "Mira")):
        npc_dir = npcs_dir / npc_id
        npc_dir.mkdir(parents=True)
        (npc_dir / "character.yaml").write_text(f"name: {label}\n", encoding="utf-8")
        (npc_dir / "description.md").write_text(f"Charakterbeschreibung {npc_id}", encoding="utf-8")
        (npc_dir / "system_prompt.md").write_text("Bleib in Character", encoding="utf-8")
        (npc_dir / "state.md").write_text(
            "---\nmood: neutral\ntrust: 50\n---\n\n- kennt den Spieler",
            encoding="utf-8",
        )
        _make_test_png(npc_dir / "img.png")

    for avatar_id, label in (("max", "Max"), ("erika", "Erika")):
        avatar_dir = avatars_dir / avatar_id
        avatar_dir.mkdir(parents=True)
        (avatar_dir / "character.yaml").write_text(f"id: {avatar_id}\nname: {label}\n", encoding="utf-8")
        (avatar_dir / "description.md").write_text(f"Avatarbeschreibung {label}", encoding="utf-8")
        _make_test_png(avatar_dir / "img.png")

    for scene_id, heading in (("office", "# Office"), ("cafe", "# Cafe")):
        scene_dir = scenes_dir / scene_id
        scene_dir.mkdir(parents=True)
        (scene_dir / "scene.md").write_text(heading, encoding="utf-8")

    active_runtime = data_npcs_dir / "vika" / "office"
    active_runtime.mkdir(parents=True, exist_ok=True)
    _make_test_png(active_runtime / "img.png")

    FakeSessionView.saved_calls = []
    FakeSessionView.npc_id = "vika"
    FakeSessionView.scene_id = "office"

    monkeypatch.setattr(config, "NPC_DIR", npcs_dir)
    monkeypatch.setattr(config, "AVATAR_DIR", avatars_dir)
    monkeypatch.setattr(config, "SCENE_DIR", scenes_dir)
    monkeypatch.setattr(config, "DATA_NPC_DIR", data_npcs_dir)
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", overrides_npcs_dir)
    monkeypatch.setattr(config, "OVERRIDES_AVATAR_DIR", overrides_avatars_dir)
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", overrides_scenes_dir)
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "WEB_DEBUG", web_debug)
    _write_session(tmp_path, "vika", "office")
    _patch_npc_turn_service(monkeypatch, FakeNpcTurnService)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", lambda turn_messages: iter(["Antwort", " vom Web"]))

    storage.npc.stm.save(
        [
            Message(id="m1", timestamp_utc="2026-03-22T10:00:00+00:00", role="user", content="Hi"),
            Message(id="m2", timestamp_utc="2026-03-22T10:01:00+00:00", role="assistant", content="Hallo."),
        ]
    )


def _request(path: str, method: str = "GET"):
    return cast(
        Any,
        SimpleNamespace(
            url=SimpleNamespace(path=path, scheme="http", netloc="testserver"),
            method=method,
            headers={},
            client=SimpleNamespace(host="testclient"),
        ),
    )


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


def _as_payload(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


def _read_stream_events(response) -> list[dict[str, object]]:
    return [json.loads(chunk) for chunk in response.body_iterator]


def _make_user_visible_runtime_error(detail: str) -> RuntimeError:
    try:
        raise openai.OpenAIError("upstream")
    except openai.OpenAIError as cause:
        try:
            raise RuntimeError(detail) from cause
        except RuntimeError as exc:
            return exc


def _make_user_visible_http_runtime_error(detail: str) -> RuntimeError:
    response = requests.Response()
    response.status_code = 404
    response.url = "https://example.com/moderated_content.png"
    cause = requests.HTTPError("404 Not Found", response=response)
    try:
        raise cause
    except requests.HTTPError as exc:
        try:
            raise RuntimeError(detail) from exc
        except RuntimeError as wrapped:
            return wrapped


async def _apply_headers(path: str, response, method: str = "GET"):
    async def call_next(_request):
        return response

    return await web_app_module._add_web_headers(_request(path, method), call_next)


def test_index_serves_gui(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    content = (web_app_module.STATIC_DIR / "index.html").read_text(encoding="utf-8")

    assert "Social Game GUI" in content
    assert 'id="root"' in content


def test_sg_routes_always_serve_spa_index(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeScheduler:
        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        for path in (
            "/sg",
            "/sg/",
            "/sg/ursula/event/options",
            "/sg/ursula/event/options/context",
            "/sg/ursula/event/options/history",
            "/sg/anything/else",
        ):
            response = client.get(path)
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/html")
            assert "<div id=\"root\"></div>" in response.text


def test_security_headers_are_present_on_index(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    response = _run_async(_apply_headers("/", web_app_module._problem_response(200, {})))

    csp = response.headers.get("content-security-policy", "")
    assert "script-src 'self'" in csp, "CSP fehlt script-src 'self'"
    assert "media-src 'self'" in csp, "CSP fehlt media-src 'self'"
    assert "object-src 'none'" in csp, "CSP fehlt object-src 'none'"
    assert "frame-ancestors 'none'" in csp, "CSP fehlt frame-ancestors"
    assert "require-trusted-types-for" not in csp, "Trusted Types sollte nicht erzwungen sein"
    assert "trusted-types " not in csp, "Trusted Types Policy sollte nicht gesetzt sein"

    assert response.headers.get("x-frame-options", "").upper() == "DENY"
    assert response.headers.get("x-content-type-options", "").lower() == "nosniff"

    hsts = response.headers.get("strict-transport-security", "")
    assert "max-age=" in hsts, "HSTS fehlt max-age"
    max_age = int(next(p.split("=")[1] for p in hsts.split(";") if "max-age" in p.strip().lower()))
    assert max_age >= 31536000, f"HSTS max-age zu kurz: {max_age}"
    assert "includesubdomains" in hsts.lower(), "HSTS fehlt includeSubDomains"

    assert response.headers.get("cross-origin-opener-policy", "").lower() == "same-origin"


def test_security_headers_are_present_on_api_routes(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    response = _run_async(_apply_headers("/api/state", web_app_module._problem_response(200, {})))

    assert "content-security-policy" in response.headers
    assert "x-frame-options" in response.headers
    assert "strict-transport-security" in response.headers
    assert "cross-origin-opener-policy" in response.headers


def test_static_assets_get_cache_headers(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    for path in ("/css/app.css", "/js/sg-app.js"):
        response = _run_async(_apply_headers(path, web_app_module._problem_response(200, {})))
        cache = response.headers.get("cache-control", "")
        assert "max-age" in cache, f"Cache-Control fehlt für {path}"


def test_static_assets_disable_cache_in_web_debug_mode(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch, web_debug=True)

    for path in ("/css/app.css", "/js/sg-app.js"):
        response = _run_async(_apply_headers(path, web_app_module._problem_response(200, {})))
        assert response.headers.get("cache-control") == "no-cache, no-store, must-revalidate"
        assert response.headers.get("pragma") == "no-cache"
        assert response.headers.get("expires") == "0"


def test_api_responses_are_not_cached(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/session")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["expires"] == "0"


def test_history_endpoint_returns_empty_list_when_git_init_fails(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    import engine.services.history_service as history_service_module

    def fail_git_init(*args, **kwargs):
        raise PermissionError("read-only volume")

    monkeypatch.setattr(history_service_module.subprocess, "run", fail_git_init)

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/session/history")

    assert response.status_code == 200
    assert response.json() == {"checkpoints": []}


def test_get_state_returns_session_messages_options_and_image(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    (tmp_path / "npcs" / "vika" / "video.mp4").write_bytes(b"video")
    storage.npc.backup_dir.mkdir(parents=True)
    _make_test_png(storage.npc.backup_dir / "img-20260510-100000.png")
    _make_test_png(storage.npc.backup_dir / "img-20260510-110000.png")

    payload = _as_payload(web_app_module.session.get_state())
    assert payload["npc"] == "vika"
    assert payload["scene"] == "office"
    assert payload["default_npc"] == config.DEFAULT_NPC_ID
    assert payload["default_scene"] == config.DEFAULT_SCENE_ID
    assert "npc_name" not in payload
    assert "character_description" not in payload
    assert "character_data" not in payload
    assert "is_dynamic_npc" not in payload
    assert "is_dynamic_scene" not in payload
    assert "image_url" not in payload
    assert "image_original_url" not in payload
    assert "image_backups" not in payload
    assert isinstance(payload["image_is_original"], bool)
    assert payload["messages"][0]["content"] == "Hi"
    assert "npcs" not in payload
    assert "scenes" not in payload


def test_npc_options_endpoint_lists_npcs_with_media_urls(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    (tmp_path / "npcs" / "vika" / "video.mp4").write_bytes(b"video")

    payload = [_as_payload(entry) for entry in web_app_module.npc.list_options()]

    npc_options = {(entry["id"], entry["name"]) for entry in payload}
    assert {("mira", "Mira"), ("vika", "Vika")}.issubset(npc_options)
    vika_option = next(entry for entry in payload if entry["id"] == "vika")
    mira_option = next(entry for entry in payload if entry["id"] == "mira")
    assert "video_url" not in vika_option
    assert "video_url" not in mira_option


def test_scene_options_endpoint_lists_scenes_with_image_urls(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    payload = [_as_payload(entry) for entry in web_app_module.scene.list_options()]

    scene_options = {(entry["id"], entry["name"]) for entry in payload}
    assert {
        ("cafe", "Cafe"),
        ("office", "Office"),
    }.issubset(scene_options)


def test_get_state_returns_context_message_when_history_is_empty(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.npc.stm.save([])

    payload = _as_payload(web_app_module.session.get_state())
    assert len(payload["messages"]) == 3
    character_message = payload["messages"][0]
    scene_message = payload["messages"][1]
    state_message = payload["messages"][2]
    assert character_message["id"] == "context-character"
    assert scene_message["id"] == "context-scene"
    assert state_message["id"] == "context-state"
    assert character_message["role"] == "assistant"
    assert scene_message["role"] == "assistant"
    assert state_message["role"] == "assistant"
    assert character_message["content"] == ""
    assert scene_message["content"] == ""
    assert state_message["content"] == ""
    assert "Charakterbeschreibung vika" in character_message["html"]
    assert "Office" in scene_message["html"]
    assert "kennt den Spieler" in state_message["html"]
    assert "<pre>" in state_message["html"]
    assert "mood: neutral" in state_message["html"]
    assert "<li>kennt den Spieler</li>" in state_message["html"]


def test_get_state_prefers_real_messages_over_context_fallback(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    payload = _as_payload(web_app_module.session.get_state())
    assert len(payload["messages"]) == 2
    assert payload["messages"][0]["content"] == "Hi"
    assert payload["messages"][1]["content"] == "Hallo."


def test_get_state_returns_context_message_when_only_system_messages_exist(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.npc.stm.save(
        [
            Message(
                id="m-system",
                timestamp_utc="2026-03-22T09:59:00+00:00",
                role="system",
                content="Interner Zustand",
            )
        ]
    )

    payload = _as_payload(web_app_module.session.get_state())
    assert len(payload["messages"]) == 3
    assert payload["messages"][0]["id"] == "context-character"
    assert payload["messages"][1]["id"] == "context-scene"
    assert payload["messages"][2]["id"] == "context-state"
    assert "Charakterbeschreibung vika" in payload["messages"][0]["html"]
    assert "Office" in payload["messages"][1]["html"]
    assert "kennt den Spieler" in payload["messages"][2]["html"]
    assert "<pre>" in payload["messages"][2]["html"]
    assert "<li>kennt den Spieler</li>" in payload["messages"][2]["html"]


def test_get_state_context_html_keeps_markdown_links_unescaped(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.npc.description.save("[link](javascript:alert('x'))")
    storage.scene.location.runtime.save("Szene [ok](https://example.com)")
    storage.npc.stm.save([])

    payload = _as_payload(web_app_module.session.get_state())
    character_html = payload["messages"][0]["html"]
    assert "javascript:" in character_html


def test_get_state_context_html_renders_label_lists_as_html_lists(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.npc.description.save("Außen:\n\n- direkt\n- offen")
    storage.npc.stm.save([])

    payload = _as_payload(web_app_module.session.get_state())
    character_html = payload["messages"][0]["html"]
    assert "<ul>" in character_html
    assert "<li>direkt</li>" in character_html
    assert "<li>offen</li>" in character_html


def test_update_session_persists_and_returns_new_state(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    payload = _as_payload(
        web_app_module.session.update_session(web_app_module.session.SessionRequest(npc="mira", scene="cafe", avatar="erika"))
    )
    assert storage.session.npc_id == "mira"
    assert storage.session.scene_id == "cafe"
    assert storage.session.avatar_id == "erika"
    assert payload["npc"] == "mira"
    assert payload["scene"] == "cafe"
    assert payload["avatar"] == "erika"


def test_update_session_avatar_switch_does_not_trigger_context_actions(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    calls: list[str] = []

    class FakeScheduler:
        def enqueue(self, job_name: str) -> None:
            calls.append(job_name)

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())
    monkeypatch.setattr(web_app_module.session.NpcSceneService, "adapt_default_fallback", lambda self: calls.append("adapt"))

    payload = _as_payload(web_app_module.session.update_session(web_app_module.session.SessionRequest(avatar="erika")))

    assert payload["avatar"] == "erika"
    assert calls == []


def test_invalid_avatar_session_value_resets_to_default(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    config.SESSION_PATH.write_text("npc_id: vika\nscene_id: office\navatar_id: missing\n", encoding="utf-8")

    assert storage.session.avatar_id == config.DEFAULT_AVATAR_ID
    assert "avatar_id: max" in config.SESSION_PATH.read_text(encoding="utf-8")


def test_avatar_list_contains_defaults_sorted_by_name(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    payload = [avatar.model_dump() for avatar in web_app_module.avatar.list_options()]

    assert [avatar["name"] for avatar in payload] == ["Erika", "Max"]
    assert {avatar["id"] for avatar in payload} == {"erika", "max"}


def test_update_session_enqueues_image_job_when_autogenerate_enabled(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.session.image_autogenerate = False
    calls: list[str] = []

    class FakeScheduler:
        def enqueue(self, job_name: str) -> None:
            calls.append(job_name)

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    payload = _as_payload(web_app_module.session.update_session(web_app_module.session.SessionRequest(image_autogenerate=True)))

    assert payload["image_autogenerate"] is True
    assert calls == ["image"]


def test_update_session_without_fields_keeps_state_unchanged(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeScheduler:
        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.put("/api/session", json={})

    assert response.status_code == 200
    payload = response.json()
    assert payload["npc"] == "vika"
    assert payload["scene"] == "office"


def test_reset_active_npc_runtime_data_deletes_directory(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    scene_data_dir = tmp_path / ".data" / "npcs" / "vika" / "office"
    other_scene_data_dir = tmp_path / ".data" / "npcs" / "vika" / "cafe"
    scene_data_dir.mkdir(parents=True, exist_ok=True)
    other_scene_data_dir.mkdir(parents=True, exist_ok=True)
    assert scene_data_dir.exists()
    assert other_scene_data_dir.exists()

    calls: list[str] = []

    class FakeScheduler:
        def clear_pending_jobs(self) -> None:
            calls.append("clear_pending_jobs")

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    response = web_app_module.npc.reset_active("vika")

    assert not scene_data_dir.exists()
    assert not other_scene_data_dir.exists()
    assert calls == ["clear_pending_jobs"]
    assert response.status_code == 200


def test_reset_active_npc_deletes_npc_scene_context(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    npc_scene_context_dir = tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / "office"
    npc_scene_context_dir.mkdir(parents=True, exist_ok=True)
    (npc_scene_context_dir / "scene.md").write_text("Kontext", encoding="utf-8")

    calls: list[str] = []

    class FakeScheduler:
        def clear_pending_jobs(self) -> None:
            calls.append("clear_pending_jobs")

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    response = web_app_module.npc.reset_active("vika")

    assert calls == ["clear_pending_jobs"]
    assert not npc_scene_context_dir.exists()
    assert storage.session.npc_id == "vika"
    assert storage.session.scene_id == "office"
    assert response.status_code == 200


def test_delete_dynamic_npc_removes_artifacts_and_resets_session(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    dynamic_npc_id = "created_lina"
    _write_session(tmp_path, dynamic_npc_id, "office")

    dynamic_npc_dir = tmp_path / ".overrides" / "npcs" / dynamic_npc_id
    dynamic_npc_dir.mkdir(parents=True)
    (dynamic_npc_dir / "character.yaml").write_text("name: Lina\n", encoding="utf-8")
    (dynamic_npc_dir / "description.md").write_text("Beschreibung", encoding="utf-8")
    (dynamic_npc_dir / "state.md").write_text("---\nmood: neutral\n---\n", encoding="utf-8")
    _make_test_png(dynamic_npc_dir / "img.png")

    dynamic_runtime_dir = tmp_path / ".data" / "npcs" / dynamic_npc_id
    active_runtime = dynamic_runtime_dir / "office"
    active_runtime.mkdir(parents=True, exist_ok=True)
    (active_runtime / "stm.jsonl").write_text("{}\n", encoding="utf-8")

    calls: list[str] = []

    class FakeScheduler:
        def clear_pending_jobs(self) -> None:
            calls.append("clear_pending_jobs")

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    response = web_app_module.npc.delete(dynamic_npc_id)

    assert calls == ["clear_pending_jobs"]
    assert not dynamic_npc_dir.exists()
    assert not dynamic_runtime_dir.exists()
    assert storage.session.npc_id == config.DEFAULT_NPC_ID
    assert response.status_code == 200


def test_update_standard_avatar_writes_override_without_renaming(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    payload = _as_payload(
        web_app_module.avatar.update(
            "max",
            web_app_module.avatar.AvatarUpdateRequest(description="Neue Beschreibung", image_data_url=None),
        )
    )

    override_dir = config.OVERRIDES_AVATAR_DIR / "max"
    assert payload["id"] == "max"
    assert payload["name"] == "Max"
    assert (override_dir / "description.md").read_text(encoding="utf-8") == "Neue Beschreibung\n"
    assert (override_dir / "character.yaml").read_text(encoding="utf-8") == "id: max\nname: Max\n"
    assert (override_dir / "img.png").is_file()


def test_reset_standard_avatar_removes_override(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    override_dir = config.OVERRIDES_AVATAR_DIR / "max"
    override_dir.mkdir(parents=True)
    (override_dir / "character.yaml").write_text("id: max\nname: Max Override\n", encoding="utf-8")
    (override_dir / "description.md").write_text("Override", encoding="utf-8")
    _make_test_png(override_dir / "img.png")

    response = web_app_module.avatar.reset_active("max")

    assert response.status_code == 200
    assert not override_dir.exists()
    assert storage.avatar.description.get() == "Avatarbeschreibung Max"


def test_reset_dynamic_avatar_is_rejected(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    avatar_dir = config.OVERRIDES_AVATAR_DIR / "alex"
    avatar_dir.mkdir(parents=True)
    (avatar_dir / "character.yaml").write_text("id: alex\nname: Alex\n", encoding="utf-8")
    (avatar_dir / "description.md").write_text("Alex", encoding="utf-8")
    _make_test_png(avatar_dir / "img.png")

    try:
        web_app_module.avatar.reset_active("alex")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "zurückgesetzt" in str(exc.detail)
    else:
        raise AssertionError("Eigener Avatar darf nicht zurückgesetzt werden.")


def test_create_avatar_sets_active_session_and_has_image(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    from engine.services.avatar_service import AvatarService

    def fake_avatar_create(self, character_description: str, avatar_image_bytes: bytes | None = None):
        avatar_dir = config.OVERRIDES_AVATAR_DIR / "alex"
        avatar_dir.mkdir(parents=True, exist_ok=True)
        (avatar_dir / "character.yaml").write_text("id: alex\nname: Alex\n", encoding="utf-8")
        (avatar_dir / "description.md").write_text(character_description, encoding="utf-8")
        (avatar_dir / "img.png").write_bytes(avatar_image_bytes or b"test-image-data")
        return avatar_dir

    monkeypatch.setattr(AvatarService, "create_override", fake_avatar_create)

    payload = _as_payload(web_app_module.avatar.create(web_app_module.avatar.AvatarCreateRequest(description="Alex")))

    assert payload["id"] == "alex"
    assert storage.session.avatar_id == "alex"
    assert (config.OVERRIDES_AVATAR_DIR / "alex" / "img.png").is_file()


def test_delete_standard_avatar_is_rejected(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    try:
        web_app_module.avatar.delete("max")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "Standard-Avatar" in str(exc.detail)
    else:
        raise AssertionError("Standard-Avatar darf nicht gelöscht werden.")


def test_delete_active_dynamic_avatar_removes_artifacts_and_resets_session(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    avatar_dir = config.OVERRIDES_AVATAR_DIR / "alex"
    avatar_dir.mkdir(parents=True)
    (avatar_dir / "character.yaml").write_text("id: alex\nname: Alex\n", encoding="utf-8")
    (avatar_dir / "description.md").write_text("Alex", encoding="utf-8")
    _make_test_png(avatar_dir / "img.png")
    storage.session.avatar_id = "alex"

    response = web_app_module.avatar.delete("alex")

    assert response.status_code == 200
    assert not avatar_dir.exists()
    assert storage.session.avatar_id == config.DEFAULT_AVATAR_ID


def test_delete_dynamic_scene_removes_artifacts_and_resets_session(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    dynamic_scene_id = "created_rooftop"
    _write_session(tmp_path, "vika", dynamic_scene_id)

    dynamic_scene_dir = tmp_path / ".overrides" / "scenes" / dynamic_scene_id
    dynamic_scene_dir.mkdir(parents=True)
    (dynamic_scene_dir / "scene.md").write_text("# Rooftop", encoding="utf-8")
    _make_test_png(dynamic_scene_dir / "img.png")

    active_runtime = tmp_path / ".data" / "npcs" / "vika" / dynamic_scene_id
    other_runtime = tmp_path / ".data" / "npcs" / "mira" / dynamic_scene_id
    active_runtime.mkdir(parents=True, exist_ok=True)
    other_runtime.mkdir(parents=True, exist_ok=True)
    (active_runtime / "stm.jsonl").write_text("{}\n", encoding="utf-8")

    active_npc_scene_override = tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / dynamic_scene_id
    other_npc_scene_override = tmp_path / ".overrides" / "npcs" / "mira" / "scenes" / dynamic_scene_id
    active_npc_scene_override.mkdir(parents=True, exist_ok=True)
    other_npc_scene_override.mkdir(parents=True, exist_ok=True)
    (active_npc_scene_override / "scene.md").write_text("vika", encoding="utf-8")
    (other_npc_scene_override / "scene.md").write_text("mira", encoding="utf-8")

    calls: list[str] = []

    class FakeScheduler:
        def clear_pending_jobs(self) -> None:
            calls.append("clear_pending_jobs")

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    response = web_app_module.scene.delete(dynamic_scene_id)

    assert calls == ["clear_pending_jobs"]
    assert not dynamic_scene_dir.exists()
    assert not active_runtime.exists()
    assert not other_runtime.exists()
    assert not active_npc_scene_override.exists()
    assert not other_npc_scene_override.exists()
    assert storage.session.npc_id == "vika"
    assert storage.session.scene_id == config.DEFAULT_SCENE_ID
    assert response.status_code == 200


def test_get_npc_returns_static_npc_properties(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    (tmp_path / "npcs" / "vika" / "video.mp4").write_bytes(b"video")

    payload = _as_payload(web_app_module.npc.get_npc("vika"))

    assert payload["name"] == "Vika"
    assert payload["description"] == "Charakterbeschreibung vika"
    assert "image_is_original" not in payload
    assert payload["is_dynamic_npc"] is False


def test_get_scene_returns_static_scene_properties(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    payload = _as_payload(web_app_module.scene.get_scene("office"))

    assert payload["id"] == "office"
    assert payload["name"] == "Office"
    assert payload["description_html"]
    assert payload["description"].startswith("# Office")
    assert payload["is_dynamic_scene"] is False


def test_reset_active_scene_resets_standard_scene_artifacts(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    scene_override_dir = tmp_path / ".overrides" / "scenes" / "office"
    scene_override_dir.mkdir(parents=True)
    (scene_override_dir / "scene.md").write_text("# Override", encoding="utf-8")
    _make_test_png(scene_override_dir / "img.png")

    runtime_dir = tmp_path / ".data" / "npcs" / "vika" / "office"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "stm.jsonl").write_text("{}\n", encoding="utf-8")

    npc_scene_override = tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / "office"
    npc_scene_override.mkdir(parents=True, exist_ok=True)
    (npc_scene_override / "scene.md").write_text("Kontext", encoding="utf-8")

    calls: list[str] = []

    class FakeScheduler:
        def clear_pending_jobs(self) -> None:
            calls.append("clear_pending_jobs")

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    response = web_app_module.scene.reset_active("office")

    assert calls == ["clear_pending_jobs"]
    assert not scene_override_dir.exists()
    assert not runtime_dir.exists()
    assert not npc_scene_override.exists()
    assert storage.session.scene_id == "office"
    assert response.status_code == 200


def test_reset_active_scene_rejects_dynamic_scene(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    dynamic_scene_id = "created_rooftop"
    _write_session(tmp_path, "vika", dynamic_scene_id)

    dynamic_scene_dir = tmp_path / ".overrides" / "scenes" / dynamic_scene_id
    dynamic_scene_dir.mkdir(parents=True)
    (dynamic_scene_dir / "scene.md").write_text("# Rooftop", encoding="utf-8")

    class FakeScheduler:
        def clear_pending_jobs(self) -> None:
            pass

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    try:
        web_app_module.scene.reset_active(dynamic_scene_id)
        raise AssertionError("Expected ValueError")
    except ValueError as exc:
        assert str(exc) == "Aktive Szene kann nicht zurückgesetzt werden."


def test_delete_scene_keeps_default_scene_and_resets_artifacts(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    scene_override_dir = tmp_path / ".overrides" / "scenes" / "office"
    scene_override_dir.mkdir(parents=True)
    (scene_override_dir / "scene.md").write_text("# Override", encoding="utf-8")

    runtime_dir = tmp_path / ".data" / "npcs" / "vika" / "office"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "stm.jsonl").write_text("{}\n", encoding="utf-8")

    class FakeScheduler:
        def clear_pending_jobs(self) -> None:
            pass

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    response = web_app_module.scene.delete("office")

    assert response.status_code == 200
    assert storage.session.scene_id == "office"
    assert not scene_override_dir.exists()
    assert not runtime_dir.exists()


def test_current_image_serves_active_npc_image(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    response = web_app_module.session.image_current()

    assert response.status_code == 200
    assert response.media_type == "image/webp"
    assert len(response.body) > 0


def test_current_image_returns_404_when_missing(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    runtime_image = storage.npc.img_runtime.path
    root_image = storage.npc.img_original.path
    if runtime_image.exists():
        runtime_image.unlink()
    if root_image.exists():
        root_image.unlink()

    try:
        web_app_module.session.image_current()
        raise AssertionError("Expected FileNotFoundError")
    except FileNotFoundError as exc:
        assert exc.filename == str(storage.npc.img.get())


def test_image_backup_endpoint_serves_active_npc_backup(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.npc.backup_dir.mkdir(parents=True)
    _make_test_png(storage.npc.backup_dir / "img-20260510-110000.png")

    response = web_app_module.session.image_current_backup("img-20260510-110000.png")

    assert response.status_code == 200
    assert response.media_type == "image/webp"
    assert len(response.body) > 0


def test_image_backup_endpoint_rejects_unknown_name(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    try:
        web_app_module.session.image_current_backup("state.md")
        raise AssertionError("Expected HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Backup-Bild nicht gefunden."


def test_image_backup_endpoint_rejects_path_traversal(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.npc.backup_dir.mkdir(parents=True)
    _make_test_png(storage.npc.backup_dir / "img-20260510-110000.png")

    for backup_name in ("img-../session.yaml.png", "img-20260510-110000/../../session.yaml.png"):
        try:
            web_app_module.session.image_current_backup(backup_name)
            raise AssertionError("Expected HTTPException")
        except HTTPException as exc:
            assert exc.status_code == 404
            assert exc.detail == "Backup-Bild nicht gefunden."


def test_npc_option_image_endpoint_accepts_cache_buster_query(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    _make_test_png(tmp_path / "npcs" / "vika" / "img.png")

    class FakeScheduler:
        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/npcs/vika/image/original?v=123")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/webp")
    assert response.content


def test_npc_option_video_endpoint_accepts_cache_buster_query(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    (tmp_path / "npcs" / "vika" / "video.mp4").write_bytes(b"video")

    class FakeScheduler:
        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/npcs/vika/video?v=123")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("video/mp4")
    assert response.content == b"video"


def test_npc_option_video_uses_storage_node(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    source = (Path(__file__).parents[1] / "engine" / "api" / "npc.py").read_text(encoding="utf-8")
    helper_source = source[source.find("def _npc_option_video(npc: EntityId):"):source.find("def _map_npc_response")]
    assert ".video" in helper_source
    assert "OVERRIDES_NPC_DIR" not in helper_source
    assert "NPC_DIR" not in helper_source


def test_scene_option_image_endpoint_accepts_cache_buster_query(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    _make_test_png(tmp_path / "scenes" / "office" / "img.png")

    class FakeScheduler:
        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/scenes/office/image?v=123")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/webp")
    assert response.content


def test_npc_option_image_endpoint_scales_width_to_256(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    _make_test_png(tmp_path / "npcs" / "vika" / "img.png", width=400, height=200)

    class FakeScheduler:
        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/npcs/vika/image/original?v=123")

    assert response.status_code == 200
    with Image.open(BytesIO(response.content)) as image:
        assert image.width == 256
        assert image.height == 128


def test_scene_option_image_endpoint_scales_width_to_256(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    _make_test_png(tmp_path / "scenes" / "office" / "img.png", width=250, height=150)

    class FakeScheduler:
        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/scenes/office/image?v=123")

    assert response.status_code == 200
    with Image.open(BytesIO(response.content)) as image:
        assert image.width == 250
        assert image.height == 150


def test_refresh_active_image_uses_character_image_service_directly(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    calls: list[str] = []

    class FakeImageService:
        def update_from_context(self, force: bool = False) -> None:
            assert force is True
            calls.append("update_from_context")

    _patch_image_service(monkeypatch, FakeImageService)

    response = _as_payload(web_app_module.session.image_current_refresh())

    assert response == {}
    assert calls == ["update_from_context"]


def test_refresh_active_image_returns_400_with_detail_for_user_visible_llm_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeImageService:
        def update_from_context(self, force: bool = False) -> None:
            assert force is True
            raise _make_user_visible_runtime_error("Anfrage durch Moderation blockiert.")

    _patch_image_service(monkeypatch, FakeImageService)

    try:
        web_app_module.session.image_current_refresh()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/session/image/refresh", "POST"), exc))

    assert response.status_code == 400
    assert response.media_type == "application/problem+json"
    assert b"Anfrage durch Moderation blockiert." in response.body


def test_refresh_active_image_returns_500_on_internal_schedule_runtime_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeImageService:
        def update_from_context(self, force: bool = False) -> None:
            assert force is True
            raise RuntimeError("generation_failed")

    _patch_image_service(monkeypatch, FakeImageService)

    try:
        web_app_module.session.image_current_refresh()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/session/image/refresh", "POST"), exc))

    assert response.status_code == 500
    assert response.media_type == "application/problem+json"
    assert b"Interner Serverfehler." in response.body
    assert b"generation_failed" not in response.body


def test_refresh_active_image_returns_400_with_detail_for_user_visible_http_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeImageService:
        def update_from_context(self, force: bool = False) -> None:
            assert force is True
            raise _make_user_visible_http_runtime_error("Anfrage durch Moderation blockiert.")

    _patch_image_service(monkeypatch, FakeImageService)

    try:
        web_app_module.session.image_current_refresh()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/session/image/refresh", "POST"), exc))

    assert response.status_code == 400
    assert response.media_type == "application/problem+json"
    assert b"Anfrage durch Moderation blockiert." in response.body


def test_refresh_active_image_returns_400_with_detail_for_direct_openai_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakePermissionDenied(openai.OpenAIError):
        pass

    class FakeImageService:
        def update_from_context(self, force: bool = False) -> None:
            assert force is True
            raise FakePermissionDenied(
                "PermissionDeniedError(\"Error code: 403 - {'code': 'The caller does not have permission to execute "
                "the specified operation', 'error': 'Content violates usage guidelines. Failed check: "
                "SAFETY_CHECK_TYPE_CSAM'}\")"
            )

    _patch_image_service(monkeypatch, FakeImageService)

    try:
        web_app_module.session.image_current_refresh()
        raise AssertionError("Expected FakePermissionDenied")
    except FakePermissionDenied as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/session/image/refresh", "POST"), exc))

    assert response.status_code == 400
    assert response.media_type == "application/problem+json"
    assert b"Content violates usage guidelines." in response.body


def test_revert_active_image_calls_character_image_service(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    calls: list[str] = []

    class FakeImageService:
        def revert(self) -> None:
            calls.append("revert")

    _patch_image_service(monkeypatch, FakeImageService)

    response = _as_payload(web_app_module.session.image_current_revert())

    assert response == {}
    assert calls == ["revert"]


def test_revert_active_image_returns_500_on_internal_runtime_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeImageService:
        def revert(self) -> None:
            raise RuntimeError("revert_failed")

    _patch_image_service(monkeypatch, FakeImageService)

    try:
        web_app_module.session.image_current_revert()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/session/image/revert", "POST"), exc))

    assert response.status_code == 500
    assert response.media_type == "application/problem+json"
    assert b"Interner Serverfehler." in response.body
    assert b"revert_failed" not in response.body


def test_delete_active_image_calls_character_image_service_and_returns_state(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    calls: list[str] = []

    class FakeImageService:
        def delete_current(self) -> None:
            calls.append("delete_current")

    _patch_image_service(monkeypatch, FakeImageService)

    response = web_app_module.session.image_current_delete()

    assert calls == ["delete_current"]
    assert response.status_code == 200


def test_delete_active_image_returns_500_on_internal_runtime_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeImageService:
        def delete_current(self) -> None:
            raise RuntimeError("delete_failed")

    _patch_image_service(monkeypatch, FakeImageService)

    try:
        web_app_module.session.image_current_delete()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/session/image/delete", "DELETE"), exc))

    assert response.status_code == 500
    assert response.media_type == "application/problem+json"
    assert b"Interner Serverfehler." in response.body
    assert b"delete_failed" not in response.body


def test_chat_stream_scheduled_tools_nach_finaler_nachricht(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    captured: dict[str, object] = {}
    calls: list[str] = []

    class FakeStreamingResponse:
        def __init__(self, content, media_type: str):
            self.status_code = 200
            self.media_type = media_type
            self.body_iterator = content

    class FakeScheduler:
        def enqueue_all(self) -> None:
            calls.append("enqueue_all")

    def fake_stream_prompt(turn_messages):
        captured["turn_messages"] = turn_messages
        return iter(["Antwort", " vom Web"])

    _patch_streaming_response(monkeypatch, FakeStreamingResponse)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", fake_stream_prompt)
    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    response = web_app_module.chat.stream(web_app_module.chat.ChatRequest(message="Startbild bitte"))

    assert response.status_code == 200
    assert _read_stream_events(response) == [
        {"type": "chunk", "delta": "Antwort"},
        {"type": "chunk", "delta": " vom Web"},
        {"type": "done"},
    ]
    assert captured["turn_messages"] == [
        {"role": "system", "content": "stub"},
        {"role": "user", "content": "Startbild bitte"},
    ]
    assert calls == ["enqueue_all"]


def test_chat_endpoint_is_not_available_anymore(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    assert all(getattr(route, "path", None) != "/api/chat" for route in web_app_module.app.routes)


def test_chat_stream_endpoint_streams_ndjson_events(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    captured: dict[str, object] = {}
    calls: list[str] = []

    class FakeStreamingResponse:
        def __init__(self, content, media_type: str):
            self.status_code = 200
            self.media_type = media_type
            self.body_iterator = content

    class FakeScheduler:
        def enqueue_all(self) -> None:
            calls.append("enqueue_all")

    def fake_stream_prompt(turn_messages):
        captured["turn_messages"] = turn_messages
        return iter(["Antwort", " vom Web"])

    _patch_streaming_response(monkeypatch, FakeStreamingResponse)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", fake_stream_prompt)
    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    response = web_app_module.chat.stream(web_app_module.chat.ChatRequest(message="Stream bitte"))

    assert response.status_code == 200
    assert response.media_type == "application/x-ndjson"
    assert captured["turn_messages"] == [
        {"role": "system", "content": "stub"},
        {"role": "user", "content": "Stream bitte"},
    ]
    assert type(response.body_iterator).__name__ == "generator"
    assert _read_stream_events(response) == [
        {"type": "chunk", "delta": "Antwort"},
        {"type": "chunk", "delta": " vom Web"},
        {"type": "done"},
    ]
    assert calls == ["enqueue_all"]


def test_chat_stream_emits_error_event_for_runtime_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    calls: list[str] = []

    class FakeStreamingResponse:
        def __init__(self, content, media_type: str):
            self.status_code = 200
            self.media_type = media_type
            self.body_iterator = content

    class FakeScheduler:
        def schedule_all(self) -> None:
            calls.append("schedule_all")

    def fake_stream_prompt(_turn_messages):
        class FailingIterator:
            def __iter__(self):
                return self

            def __next__(self):
                raise _make_user_visible_runtime_error("Kontingent erschöpft – Plan und Abrechnung prüfen.")

        return FailingIterator()

    _patch_streaming_response(monkeypatch, FakeStreamingResponse)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", fake_stream_prompt)
    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    response = web_app_module.chat.stream(web_app_module.chat.ChatRequest(message="Fehler bitte"))

    assert response.status_code == 200
    assert _read_stream_events(response) == [
        {"type": "error", "detail": "Kontingent erschöpft – Plan und Abrechnung prüfen."},
    ]
    assert calls == []


def test_chat_stream_emits_error_event_for_direct_openai_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeStreamingResponse:
        def __init__(self, content, media_type: str):
            self.status_code = 200
            self.media_type = media_type
            self.body_iterator = content

    class FakePermissionDenied(openai.OpenAIError):
        pass

    def fake_stream_prompt(_turn_messages):
        class FailingIterator:
            def __iter__(self):
                return self

            def __next__(self):
                raise FakePermissionDenied(
                    "PermissionDeniedError(\"Error code: 403 - {'code': 'The caller does not have permission to "
                    "execute the specified operation', 'error': 'Content violates usage guidelines. Failed check: "
                    "SAFETY_CHECK_TYPE_CSAM'}\")"
                )

        return FailingIterator()

    _patch_streaming_response(monkeypatch, FakeStreamingResponse)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", fake_stream_prompt)

    response = web_app_module.chat.stream(web_app_module.chat.ChatRequest(message="Fehler bitte"))

    assert response.status_code == 200
    assert _read_stream_events(response) == [
        {
            "type": "error",
            "detail": "Content violates usage guidelines.",
        },
    ]


def test_chat_stream_emits_generic_error_event_without_leaking_details(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeStreamingResponse:
        def __init__(self, content, media_type: str):
            self.status_code = 200
            self.media_type = media_type
            self.body_iterator = content

    def fake_stream_prompt(_turn_messages):
        def _iterator():
            yield "Teilantwort"
            raise ValueError("secret_backend_details")

        return _iterator()

    _patch_streaming_response(monkeypatch, FakeStreamingResponse)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", fake_stream_prompt)

    response = web_app_module.chat.stream(web_app_module.chat.ChatRequest(message="Teilantwort bitte"))

    assert response.status_code == 200
    assert _read_stream_events(response) == [
        {"type": "chunk", "delta": "Teilantwort"},
        {"type": "error", "detail": "Interner Serverfehler."},
    ]


def test_chat_stream_hides_internal_followup_runtime_errors_after_chunks(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    calls: list[str] = []

    class FakeStreamingResponse:
        def __init__(self, content, media_type: str):
            self.status_code = 200
            self.media_type = media_type
            self.body_iterator = content

    class FakeScheduler:
        def schedule_all(self) -> None:
            calls.append("schedule_all")

    class FailingStm:
        def append(self, _row):
            raise RuntimeError("internal_store_issue")

    class FailingNpcPaths:
        stm = FailingStm()

    class FailingStorage:
        npc = FailingNpcPaths()

    _patch_streaming_response(monkeypatch, FakeStreamingResponse)
    monkeypatch.setattr(npc_turn_service_module, "storage", FailingStorage())
    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    response = web_app_module.chat.stream(web_app_module.chat.ChatRequest(message="Speichern bitte"))

    assert response.status_code == 200
    assert _read_stream_events(response) == [
        {"type": "chunk", "delta": "Antwort"},
        {"type": "chunk", "delta": " vom Web"},
        {"type": "error", "detail": "Interner Serverfehler."},
    ]
    assert calls == []


def test_update_user_profile_persists_legacy_runtime_profile_but_state_uses_avatar(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    scene_profile = config.DATA_NPC_DIR / "vika" / "office" / "user_profile.md"
    (config.NPC_DIR / "user_profile.md").write_text("default", encoding="utf-8")

    payload = _as_payload(
        web_app_module.session.update_user_profile(web_app_module.session.UserProfileRequest(content="global-profile"))
    )

    assert scene_profile.read_text(encoding="utf-8") == "global-profile"
    assert payload["user_profile"] == "Avatarbeschreibung Max"


def test_chat_prompt_uses_active_avatar_description(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.session.avatar_id = "erika"
    (config.DATA_NPC_DIR / "vika" / "office" / "user_profile.md").write_text("Altes Profil", encoding="utf-8")

    prompt = npc_turn_service_module.NpcTurnService._build_system_prompt("Keine Erinnerungen")

    assert "Avatarbeschreibung Erika" in prompt
    assert "Altes Profil" not in prompt


def test_web_lifespan_uses_scheduler_directly(monkeypatch):
    events: list[str] = []

    class FakeScheduler:
        def __init__(self) -> None:
            events.append("init")

        def start(self) -> None:
            events.append("start")

        def stop(self) -> None:
            events.append("stop")

    monkeypatch.setattr(web_app_module, "Scheduler", FakeScheduler)

    async def run_lifespan():
        async with web_app_module._lifespan(web_app_module.app):
            events.append("inside")

    _run_async(run_lifespan())
    assert events == ["init", "start", "inside", "stop"]


def test_web_lifespan_creates_new_scheduler_per_run(monkeypatch):
    events: list[str] = []

    class FakeScheduler:
        def __init__(self) -> None:
            events.append("init")

        def start(self) -> None:
            events.append("start")

        def stop(self) -> None:
            events.append("stop")

    monkeypatch.setattr(web_app_module, "Scheduler", FakeScheduler)

    async def run_lifespan():
        async with web_app_module._lifespan(web_app_module.app):
            events.append("inside")

    _run_async(run_lifespan())
    _run_async(run_lifespan())
    assert events == ["init", "start", "inside", "stop", "init", "start", "inside", "stop"]


def test_create_scene_calls_scene_service(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    created_scenes: list[str] = []
    created_npc_scenes: list[tuple[str, str]] = []

    def fake_scene_create(self, short_description: str, scene_image_bytes: bytes | None = None):
        created_scenes.append(short_description)
        scene_dir = tmp_path / ".overrides" / "scenes" / "test_scene"
        scene_dir.mkdir(parents=True, exist_ok=True)
        (scene_dir / "scene.md").write_text("# Test Scene\n", encoding="utf-8")
        (scene_dir / "img.png").write_bytes(b"test-image-data")
        return scene_dir

    def fake_npc_scene_create(self, short_description: str):
        created_npc_scenes.append((short_description, storage.session.scene_id))
        return tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / storage.session.scene_id / "scene.md"

    monkeypatch.setattr(SceneService, "create_override", fake_scene_create)
    monkeypatch.setattr(NpcSceneService, "create_override", fake_npc_scene_create)

    scheduler_calls: list[tuple[str, str]] = []

    class FakeScheduler:
        def enqueue(self, job_name: str) -> None:
            scheduler_calls.append((job_name, storage.session.scene_id))

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes",
            json={
                "description": "Ein neues Café",
            }
        )

    assert response.status_code == 200
    assert created_scenes == ["Ein neues Café"]
    assert created_npc_scenes == [("Ein neues Café", "test_scene")]
    assert scheduler_calls == [("image", "test_scene")]
    assert storage.session.scene_id == "test_scene"
    assert response.json()["id"] == "test_scene"


def test_generate_scene_context_returns_preview_without_saving(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    prompts: list[str] = []

    class FakeScheduler:
        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    def fake_run_prompt_small(prompt: str) -> str:
        prompts.append(prompt)
        return "Generierter NPC-Kontext"

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())
    monkeypatch.setattr(web_app_module.client, "run_prompt_small", fake_run_prompt_small)

    with TestClient(web_app_module.app) as client:
        response = client.post("/api/session/context/generate", json={"content": "NPC sitzt am Fenster"})

    override_file = tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / "office" / "scene.md"
    assert response.status_code == 200
    assert response.json() == {"context": "Generierter NPC-Kontext"}
    assert "NPC sitzt am Fenster" in prompts[0]
    assert not override_file.exists()


def test_update_scene_context_saves_override_and_returns_updated_state(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.npc.stm.save([])

    class FakeScheduler:
        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.put("/api/session/context", json={"content": "NPC lehnt an der Bar."})

    override_file = tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / "office" / "scene.md"
    payload = response.json()
    assert response.status_code == 200
    assert override_file.read_text(encoding="utf-8") == "NPC lehnt an der Bar."
    assert payload["sceneContext"] == "NPC lehnt an der Bar."
    assert payload["messages"][1]["isEditableSceneContext"] is True
    assert "NPC lehnt an der Bar" in payload["messages"][1]["html"]


def test_create_scene_uses_same_description_for_scene_and_npc_scene(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    created_scenes: list[str] = []
    created_npc_scenes: list[str] = []

    def fake_scene_create(self, short_description: str, scene_image_bytes: bytes | None = None):
        created_scenes.append(short_description)
        scene_dir = tmp_path / ".overrides" / "scenes" / "test_scene"
        scene_dir.mkdir(parents=True, exist_ok=True)
        (scene_dir / "scene.md").write_text("# Test Scene\n", encoding="utf-8")
        (scene_dir / "img.png").write_bytes(b"test-image-data")
        return scene_dir

    def fake_npc_scene_create(self, short_description: str):
        created_npc_scenes.append(short_description)
        return tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / "test_scene" / "scene.md"

    monkeypatch.setattr(SceneService, "create_override", fake_scene_create)
    monkeypatch.setattr(NpcSceneService, "create_override", fake_npc_scene_create)

    class FakeScheduler:
        def enqueue(self, _job_name: str) -> None:
            pass

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes",
            json={
                "description": "Ein neues Café",
            }
        )

    assert response.status_code == 200
    assert created_scenes == ["Ein neues Café"]
    assert created_npc_scenes == ["Ein neues Café"]


def test_create_scene_always_creates_scene_and_npc_context(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\nimage_autogenerate: true\n", encoding="utf-8")

    created_scenes: list[str] = []
    created_npc_scenes: list[str] = []
    adapted_scenes: list[str] = []

    def fake_scene_create(self, short_description: str, scene_image_bytes: bytes | None = None):
        created_scenes.append(short_description)
        scene_dir = tmp_path / ".overrides" / "scenes" / "test_scene"
        scene_dir.mkdir(parents=True, exist_ok=True)
        return scene_dir

    def fake_npc_scene_create(self, short_description: str):
        created_npc_scenes.append(short_description)

    def fake_adapt(self):
        adapted_scenes.append(storage.session.scene_id)

    scheduler_calls: list[str] = []

    class FakeScheduler:
        def enqueue(self, job_name: str) -> None:
            scheduler_calls.append(job_name)

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    monkeypatch.setattr(SceneService, "create_override", fake_scene_create)
    monkeypatch.setattr(NpcSceneService, "create_override", fake_npc_scene_create)
    monkeypatch.setattr(NpcSceneService, "adapt_default_fallback", fake_adapt)
    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes",
            json={"description": "Ein neues Café"},
        )

    assert response.status_code == 200
    assert created_scenes == ["Ein neues Café"]
    assert created_npc_scenes == ["Ein neues Café"]
    assert adapted_scenes == ["test_scene"]
    assert scheduler_calls == ["image"]
    assert storage.session.scene_id == "test_scene"


def test_create_scene_does_not_enqueue_image_job_when_autogenerate_is_disabled(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")
    storage.session.image_autogenerate = False

    def fake_scene_create(self, _short_description: str, scene_image_bytes: bytes | None = None):
        scene_dir = tmp_path / ".overrides" / "scenes" / "test_scene"
        scene_dir.mkdir(parents=True, exist_ok=True)
        (scene_dir / "scene.md").write_text("# Test Scene\n", encoding="utf-8")
        (scene_dir / "img.png").write_bytes(b"test-image-data")
        return scene_dir

    def fake_npc_scene_create(self, _short_description: str):
        return tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / "test_scene" / "scene.md"

    monkeypatch.setattr(SceneService, "create_override", fake_scene_create)
    monkeypatch.setattr(NpcSceneService, "create_override", fake_npc_scene_create)

    scheduler_calls: list[str] = []

    class FakeScheduler:
        def enqueue(self, job_name: str) -> None:
            scheduler_calls.append(job_name)

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes",
            json={
                "description": "Ein neues Café",
            }
        )

    assert response.status_code == 200
    assert scheduler_calls == []


def test_create_scene_uses_visible_preview_image(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\nimage_autogenerate: false\n", encoding="utf-8")

    captured_images: list[bytes | None] = []

    def fake_scene_create(self, _short_description: str, scene_image_bytes: bytes | None = None):
        captured_images.append(scene_image_bytes)
        scene_dir = tmp_path / ".overrides" / "scenes" / "test_scene"
        scene_dir.mkdir(parents=True, exist_ok=True)
        if scene_image_bytes is not None:
            (scene_dir / "img.png").write_bytes(scene_image_bytes)
        return scene_dir

    monkeypatch.setattr(SceneService, "create_override", fake_scene_create)
    monkeypatch.setattr(NpcSceneService, "create_override", lambda self, _short_description: None)
    monkeypatch.setattr(NpcSceneService, "adapt_default_fallback", lambda self: None)

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes",
            json={
                "description": "Ein Café",
                "image_data_url": _test_png_data_url(width=6, height=8),
            },
        )

    assert response.status_code == 200
    assert captured_images[0] is not None
    with Image.open(BytesIO(captured_images[0] or b"")) as image:
        assert image.size == (6, 8)


def test_create_scene_generates_image_from_reference_when_no_preview_exists(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\nimage_autogenerate: false\n", encoding="utf-8")

    generated_image = base64.b64decode(_test_png_data_url(width=9, height=11).split(",", 1)[1])
    preview_calls: list[tuple[str, bytes | None]] = []
    captured_images: list[bytes | None] = []

    def fake_preview(self, scene_description: str, reference_image_bytes: bytes | None = None):
        preview_calls.append((scene_description, reference_image_bytes))
        return generated_image

    def fake_scene_create(self, _short_description: str, scene_image_bytes: bytes | None = None):
        captured_images.append(scene_image_bytes)
        scene_dir = tmp_path / ".overrides" / "scenes" / "test_scene"
        scene_dir.mkdir(parents=True, exist_ok=True)
        return scene_dir

    monkeypatch.setattr(SceneService, "create_preview_image", fake_preview)
    monkeypatch.setattr(SceneService, "create_override", fake_scene_create)
    monkeypatch.setattr(NpcSceneService, "create_override", lambda self, _short_description: None)
    monkeypatch.setattr(NpcSceneService, "adapt_default_fallback", lambda self: None)

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes",
            json={
                "description": "Ein Café",
                "reference_image_data_url": _test_png_data_url(width=5, height=7),
            },
        )

    assert response.status_code == 200
    assert preview_calls[0][0] == "Ein Café"
    assert preview_calls[0][1] is not None
    assert captured_images == [generated_image]


def test_create_scene_fails_when_reference_image_generation_fails(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    def fail_preview(self, _scene_description: str, _reference_image_bytes: bytes | None = None):
        raise RuntimeError("generation_failed")

    def fail_scene_create(self, _short_description: str, _scene_image_bytes: bytes | None = None):
        raise AssertionError("scene must not be created when automatic image generation fails")

    monkeypatch.setattr(SceneService, "create_preview_image", fail_preview)
    monkeypatch.setattr(SceneService, "create_override", fail_scene_create)

    with TestClient(web_app_module.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/scenes",
            json={
                "description": "Ein Café",
                "reference_image_data_url": _test_png_data_url(),
            },
        )

    assert response.status_code == 500


def test_describe_scene_reference_endpoint_uses_scene_service(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    seen_reference: list[bytes] = []

    def fake_describe(self, reference_image_bytes: bytes):
        seen_reference.append(reference_image_bytes)
        return "Ein heller Raum mit Pflanzen."

    monkeypatch.setattr(SceneService, "describe_reference_image", fake_describe)

    with TestClient(web_app_module.app) as client:
        describe_response = client.post("/api/scenes/image/describe", json={"image_data_url": _test_png_data_url()})

    assert describe_response.json() == {"description": "Ein heller Raum mit Pflanzen."}
    assert seen_reference


def test_scene_preview_image_endpoint_uses_scene_service(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    def fake_preview(self, scene_description: str, reference_image_bytes: bytes | None = None):
        assert scene_description == "Ein heller Raum"
        assert reference_image_bytes is not None
        return base64.b64decode(_test_png_data_url().split(",", 1)[1])

    monkeypatch.setattr(SceneService, "create_preview_image", fake_preview)

    with TestClient(web_app_module.app) as client:
        preview_response = client.post(
            "/api/scenes/image/preview",
            json={"description": "Ein heller Raum", "reference_image_data_url": _test_png_data_url()},
        )

    assert preview_response.json()["imageDataUrl"].startswith("data:image/png;base64,")


def test_create_scene_rejects_empty_scene_description(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    class FakeScheduler:
        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    import engine.api.app as web_app_module
    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes",
            json={
                "description": "   ",
            }
        )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "darf nicht leer sein" in response.json()["detail"].lower()


def test_reference_image_rejects_invalid_magic_bytes(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    image_data_url = f"data:image/png;base64,{base64.b64encode(b'not-a-png').decode('ascii')}"

    with TestClient(web_app_module.app) as client:
        response = client.post("/api/scenes/image/describe", json={"image_data_url": image_data_url})

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "ungültiges bildformat" in response.json()["detail"].lower()


def test_reference_image_rejects_images_over_3_5_mb(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    oversized_png_payload = b"\x89PNG\r\n\x1a\n" + b"x" * 3_670_017
    image_data_url = f"data:image/png;base64,{base64.b64encode(oversized_png_payload).decode('ascii')}"

    with TestClient(web_app_module.app) as client:
        response = client.post("/api/scenes/image/describe", json={"image_data_url": image_data_url})

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "3,5 mb" in response.json()["detail"].lower()


def test_create_npc_calls_npc_service_and_selects_new_npc(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.npc_service import NpcService

    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    created_npcs: list[str] = []
    adapted_npcs: list[str] = []

    def fake_npc_create(self, character_description: str, npc_image_bytes: bytes | None = None):
        created_npcs.append(character_description)
        npc_dir = tmp_path / ".overrides" / "npcs" / "alex"
        npc_dir.mkdir(parents=True, exist_ok=True)
        (npc_dir / "character.yaml").write_text("name: Alex\n", encoding="utf-8")
        (npc_dir / "description.md").write_text("# Alex\n", encoding="utf-8")
        (npc_dir / "state.md").write_text("---\ntrust: 0\n---\n", encoding="utf-8")
        (npc_dir / "img.png").write_bytes(b"test-image-data")
        return npc_dir

    def fake_adapt(self):
        adapted_npcs.append(storage.session.npc_id)

    class FakeScheduler:
        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    monkeypatch.setattr(NpcService, "create_override", fake_npc_create)
    monkeypatch.setattr(NpcSceneService, "adapt_default_fallback", fake_adapt)
    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/npcs",
            json={
                "description": "Alex, 28, arbeitet als Koch.",
            }
        )

    assert response.status_code == 200
    assert created_npcs == ["Alex, 28, arbeitet als Koch."]
    assert adapted_npcs == ["alex"]
    assert response.json()["id"] == "alex"
    assert storage.session.npc_id == "alex"


def test_create_npc_uses_visible_preview_image(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.npc_service import NpcService

    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    captured_images: list[bytes | None] = []

    def fake_npc_create(self, _character_description: str, npc_image_bytes: bytes | None = None):
        captured_images.append(npc_image_bytes)
        npc_dir = tmp_path / ".overrides" / "npcs" / "alex"
        npc_dir.mkdir(parents=True, exist_ok=True)
        (npc_dir / "character.yaml").write_text("name: Alex\n", encoding="utf-8")
        (npc_dir / "description.md").write_text("# Alex\n", encoding="utf-8")
        (npc_dir / "state.md").write_text("---\ntrust: 0\n---\n", encoding="utf-8")
        if npc_image_bytes is not None:
            (npc_dir / "img.png").write_bytes(npc_image_bytes)
        return npc_dir

    monkeypatch.setattr(NpcService, "create_override", fake_npc_create)
    monkeypatch.setattr(NpcSceneService, "adapt_default_fallback", lambda self: None)

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/npcs",
            json={"description": "Alex", "image_data_url": _test_png_data_url(width=5, height=7)},
        )

    assert response.status_code == 200
    assert captured_images[0] is not None
    with Image.open(BytesIO(captured_images[0] or b"")) as image:
        assert image.size == (5, 7)


def test_create_npc_generates_image_from_reference_when_no_preview_exists(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.npc_service import NpcService

    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    generated_image = base64.b64decode(_test_png_data_url(width=8, height=10).split(",", 1)[1])
    preview_calls: list[tuple[str, bytes | None]] = []
    captured_images: list[bytes | None] = []

    def fake_preview(self, character_description: str, reference_image_bytes: bytes | None = None):
        preview_calls.append((character_description, reference_image_bytes))
        return generated_image

    def fake_npc_create(self, _character_description: str, npc_image_bytes: bytes | None = None):
        captured_images.append(npc_image_bytes)
        npc_dir = tmp_path / ".overrides" / "npcs" / "alex"
        npc_dir.mkdir(parents=True, exist_ok=True)
        (npc_dir / "character.yaml").write_text("name: Alex\n", encoding="utf-8")
        (npc_dir / "description.md").write_text("# Alex\n", encoding="utf-8")
        (npc_dir / "state.md").write_text("---\ntrust: 0\n---\n", encoding="utf-8")
        return npc_dir

    monkeypatch.setattr(NpcService, "create_preview_image", fake_preview)
    monkeypatch.setattr(NpcService, "create_override", fake_npc_create)
    monkeypatch.setattr(NpcSceneService, "adapt_default_fallback", lambda self: None)

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/npcs",
            json={"description": "Alex", "reference_image_data_url": _test_png_data_url(width=5, height=7)},
        )

    assert response.status_code == 200
    assert preview_calls[0][0] == "Alex"
    assert preview_calls[0][1] is not None
    assert captured_images == [generated_image]


def test_create_npc_fails_when_reference_image_generation_fails(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_service import NpcService

    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    def fail_preview(self, _character_description: str, _reference_image_bytes: bytes | None = None):
        raise RuntimeError("generation_failed")

    def fail_npc_create(self, _character_description: str, _npc_image_bytes: bytes | None = None):
        raise AssertionError("npc must not be created when automatic image generation fails")

    monkeypatch.setattr(NpcService, "create_preview_image", fail_preview)
    monkeypatch.setattr(NpcService, "create_override", fail_npc_create)

    with TestClient(web_app_module.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/npcs",
            json={"description": "Alex", "reference_image_data_url": _test_png_data_url()},
        )

    assert response.status_code == 500


def test_describe_npc_reference_endpoint_uses_npc_service(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_service import NpcService

    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    seen_reference: list[bytes] = []

    def fake_describe(self, reference_image_bytes: bytes):
        seen_reference.append(reference_image_bytes)
        return "Eine Person mit dunkler Jacke."

    monkeypatch.setattr(NpcService, "describe_reference_image", fake_describe)

    with TestClient(web_app_module.app) as client:
        response = client.post("/api/npcs/image/describe", json={"image_data_url": _test_png_data_url()})

    assert response.json() == {"description": "Eine Person mit dunkler Jacke."}
    assert seen_reference


def test_npc_preview_image_endpoint_uses_npc_service(tmp_path, monkeypatch):
    import engine.api.app as web_app_module
    from engine.services.npc_service import NpcService

    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    def fake_preview(self, character_description: str, reference_image_bytes: bytes | None = None):
        assert character_description == "Eine Person mit dunkler Jacke"
        assert reference_image_bytes is not None
        return base64.b64decode(_test_png_data_url().split(",", 1)[1])

    monkeypatch.setattr(NpcService, "create_preview_image", fake_preview)

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/npcs/image/preview",
            json={"description": "Eine Person mit dunkler Jacke", "reference_image_data_url": _test_png_data_url()},
        )

    assert response.json()["imageDataUrl"].startswith("data:image/png;base64,")


def test_create_npc_rejects_empty_character_description(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    class FakeScheduler:
        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    import engine.api.app as web_app_module
    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/npcs",
            json={
                "description": "   ",
            }
        )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "darf nicht leer sein" in response.json()["detail"].lower()


def test_chat_stream_rejects_empty_message_with_validation_error(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    class FakeScheduler:
        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    import engine.api.app as web_app_module
    _patch_scheduler(monkeypatch, lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post("/api/chat/stream", json={"message": "   "})

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "darf nicht leer sein" in response.json()["detail"].lower()
