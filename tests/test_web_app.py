import asyncio
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

import engine.web.app as web_app_module
from engine.config import config
from engine.storage import storage
from engine.storage.models import Message


def _make_test_png(path: Path, width: int = 4, height: int = 4) -> Path:
    img = Image.new("RGB", (width, height), color=(80, 120, 160))
    img.save(path, format="PNG")
    return path


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


def _setup_web_app(
    tmp_path,
    monkeypatch,
    *,
    web_debug: bool = False,
) -> None:
    npcs_dir = tmp_path / "npcs"
    scenes_dir = tmp_path / "scenes"
    data_npcs_dir = tmp_path / ".data" / "npcs"
    overrides_npcs_dir = tmp_path / ".overrides" / "npcs"
    overrides_scenes_dir = tmp_path / ".overrides" / "scenes"
    overrides_npcs_dir.mkdir(parents=True, exist_ok=True)
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
    monkeypatch.setattr(config, "SCENE_DIR", scenes_dir)
    monkeypatch.setattr(config, "DATA_NPC_DIR", data_npcs_dir)
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", overrides_npcs_dir)
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", overrides_scenes_dir)
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "WEB_DEBUG", web_debug)
    _write_session(tmp_path, "vika", "office")
    monkeypatch.setattr(web_app_module, "NpcTurnService", FakeNpcTurnService)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", lambda turn_messages: iter(["Antwort", " vom Web"]))
    web_app_module.app.state.watch_scheduler = None
    web_app_module._scheduler = None

    storage.npc.stm.save(
        [
            Message(id="m1", timestamp_utc="2026-03-22T10:00:00+00:00", role="user", content="Hi"),
            Message(id="m2", timestamp_utc="2026-03-22T10:01:00+00:00", role="assistant", content="Hallo."),
        ]
    )


def _request(path: str, method: str = "GET"):
    return cast(Any, SimpleNamespace(url=SimpleNamespace(path=path), method=method))


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


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
    assert "<sg-app" in content
    assert 'src="js/sg-app.js"' in content


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


def test_get_state_returns_session_messages_options_and_image(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    (tmp_path / "npcs" / "vika" / "video.mp4").write_bytes(b"video")
    storage.npc.backup_dir.mkdir(parents=True)
    _make_test_png(storage.npc.backup_dir / "img-20260510-100000.png")
    _make_test_png(storage.npc.backup_dir / "img-20260510-110000.png")

    payload = web_app_module.get_state()
    assert payload["npc_id"] == "vika"
    assert payload["npc_name"] == "Vika"
    assert payload["character_description"] == "Charakterbeschreibung vika"
    assert payload["character_data"] == {"name": "Vika"}
    assert payload["scene_id"] == "office"
    assert payload["default_npc_id"] == config.DEFAULT_NPC_ID
    assert payload["default_scene_id"] == config.DEFAULT_SCENE_ID
    assert payload["is_dynamic_npc"] is False
    assert payload["is_dynamic_scene"] is False
    assert payload["image_url"] == "/api/image/current"
    assert payload["image_original_url"].startswith("/api/image/original?v=")
    assert [backup["name"] for backup in payload["image_backups"]] == [
        "img-20260510-110000.png",
        "img-20260510-100000.png",
    ]
    assert payload["image_backups"][0]["url"].startswith("/api/image/backups/img-20260510-110000.png?v=")
    assert payload["messages"][0]["content"] == "Hi"
    npc_options = {(entry["id"], entry["label"]) for entry in payload["npcs"]}
    assert {("mira", "Mira"), ("vika", "Vika")}.issubset(npc_options)
    vika_option = next(entry for entry in payload["npcs"] if entry["id"] == "vika")
    mira_option = next(entry for entry in payload["npcs"] if entry["id"] == "mira")
    assert vika_option["video_url"].startswith("/api/npcs/vika/video?v=")
    assert mira_option["video_url"] is None
    scene_options = {(entry["id"], entry["label"], entry["image_url"]) for entry in payload["scenes"]}
    assert {
        ("cafe", "Cafe", "/api/scenes/cafe/image?v="),
        ("office", "Office", "/api/scenes/office/image?v="),
    }.issubset(scene_options)


def test_get_state_returns_context_message_when_history_is_empty(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.npc.stm.save([])

    payload = web_app_module.get_state()
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
    payload = web_app_module.get_state()
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

    payload = web_app_module.get_state()
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
    storage.scene.scene_runtime.save("Szene [ok](https://example.com)")
    storage.npc.stm.save([])

    payload = web_app_module.get_state()
    character_html = payload["messages"][0]["html"]
    assert "javascript:" in character_html


def test_get_state_context_html_renders_label_lists_as_html_lists(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.npc.description.save("Außen:\n\n- direkt\n- offen")
    storage.npc.stm.save([])

    payload = web_app_module.get_state()
    character_html = payload["messages"][0]["html"]
    assert "<ul>" in character_html
    assert "<li>direkt</li>" in character_html
    assert "<li>offen</li>" in character_html


def test_update_session_persists_and_returns_new_state(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    payload = web_app_module.update_session(web_app_module.SessionRequest(npc_id="mira", scene_id="cafe"))
    assert storage.session.npc_id == "mira"
    assert storage.session.scene_id == "cafe"
    assert payload["npc_id"] == "mira"
    assert payload["npc_name"] == "Mira"
    assert payload["scene_id"] == "cafe"


def test_update_session_requires_at_least_one_field(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    try:
        web_app_module.update_session(web_app_module.SessionRequest())
        raise AssertionError("Expected HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail == "Mindestens npc_id, scene_id oder image_autogenerate muss gesetzt sein."


def test_reset_active_npc_runtime_data_deletes_directory(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    scene_data_dir = tmp_path / ".data" / "npcs" / "vika" / "office"
    scene_data_dir.mkdir(parents=True, exist_ok=True)
    assert scene_data_dir.exists()

    calls: list[str] = []

    class FakeScheduler:
        def clear_pending_jobs(self) -> None:
            calls.append("clear_pending_jobs")

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    payload = web_app_module.reset_active_npc_runtime_data()

    assert not scene_data_dir.exists()
    assert calls == ["clear_pending_jobs"]
    assert payload["npc_id"] == "vika"
    assert payload["scene_id"] == "office"


def test_reset_active_npc_can_delete_npc_scene_context(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    npc_scene_context_dir = tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / "office"
    npc_scene_context_dir.mkdir(parents=True, exist_ok=True)
    (npc_scene_context_dir / "scene.md").write_text("Kontext", encoding="utf-8")

    calls: list[str] = []

    class FakeScheduler:
        def clear_pending_jobs(self) -> None:
            calls.append("clear_pending_jobs")

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    payload = web_app_module.reset_active_npc_runtime_data(delete_npc_context=True)

    assert calls == ["clear_pending_jobs"]
    assert not npc_scene_context_dir.exists()
    assert storage.session.npc_id == "vika"
    assert storage.session.scene_id == "office"
    assert payload["npc_id"] == "vika"
    assert payload["scene_id"] == "office"


def test_reset_active_npc_can_delete_dynamic_npc_and_reset_session(tmp_path, monkeypatch):
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

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    payload = web_app_module.reset_active_npc_runtime_data(delete_npc=True)

    assert calls == ["clear_pending_jobs"]
    assert not dynamic_npc_dir.exists()
    assert not dynamic_runtime_dir.exists()
    assert storage.session.npc_id == config.DEFAULT_NPC_ID
    assert payload["npc_id"] == config.DEFAULT_NPC_ID
    assert payload["is_dynamic_npc"] is False


def test_reset_active_npc_can_delete_dynamic_scene_and_reset_session(tmp_path, monkeypatch):
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

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    payload = web_app_module.reset_active_npc_runtime_data(delete_scene=True)

    assert calls == ["clear_pending_jobs"]
    assert not dynamic_scene_dir.exists()
    assert not active_runtime.exists()
    assert not other_runtime.exists()
    assert not active_npc_scene_override.exists()
    assert not other_npc_scene_override.exists()
    assert storage.session.npc_id == "vika"
    assert storage.session.scene_id == config.DEFAULT_SCENE_ID
    assert payload["npc_id"] == "vika"
    assert payload["scene_id"] == config.DEFAULT_SCENE_ID
    assert payload["is_dynamic_scene"] is False


def test_current_image_serves_active_npc_image(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    response = web_app_module.current_image()

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
        web_app_module.current_image()
        raise AssertionError("Expected FileNotFoundError")
    except FileNotFoundError as exc:
        assert exc.filename == str(storage.npc.img.get())


def test_image_backup_endpoint_serves_active_npc_backup(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    storage.npc.backup_dir.mkdir(parents=True)
    _make_test_png(storage.npc.backup_dir / "img-20260510-110000.png")

    response = web_app_module.image_backup("img-20260510-110000.png")

    assert response.status_code == 200
    assert response.media_type == "image/webp"
    assert len(response.body) > 0


def test_original_image_endpoint_serves_active_npc_original(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    response = web_app_module.original_image()

    assert response.status_code == 200
    assert response.media_type == "image/webp"
    assert len(response.body) > 0


def test_image_backup_endpoint_rejects_unknown_name(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    try:
        web_app_module.image_backup("state.md")
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
            web_app_module.image_backup(backup_name)
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

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/npcs/vika/image?v=123")

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

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/npcs/vika/video?v=123")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("video/mp4")
    assert response.content == b"video"


def test_npc_option_video_uses_storage_node(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    source = (Path(__file__).parents[1] / "engine" / "web" / "app.py").read_text(encoding="utf-8")
    helper_source = source[source.find("def _npc_option_video(npc_id: str):"):source.find("def _npc_option_video_url")]
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

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

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

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/npcs/vika/image?v=123")

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

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

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

    monkeypatch.setattr(web_app_module, "ImageService", FakeImageService)

    response = web_app_module.refresh_active_image()

    assert response == {}
    assert calls == ["update_from_context"]


def test_refresh_active_image_returns_400_with_detail_for_user_visible_llm_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeImageService:
        def update_from_context(self, force: bool = False) -> None:
            assert force is True
            raise _make_user_visible_runtime_error("Anfrage durch Moderation blockiert.")

    monkeypatch.setattr(web_app_module, "ImageService", FakeImageService)

    try:
        web_app_module.refresh_active_image()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/image/refresh-active", "POST"), exc))

    assert response.status_code == 400
    assert response.media_type == "application/problem+json"
    assert b"Anfrage durch Moderation blockiert." in response.body


def test_refresh_active_image_returns_500_on_internal_schedule_runtime_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeImageService:
        def update_from_context(self, force: bool = False) -> None:
            assert force is True
            raise RuntimeError("generation_failed")

    monkeypatch.setattr(web_app_module, "ImageService", FakeImageService)

    try:
        web_app_module.refresh_active_image()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/image/refresh-active", "POST"), exc))

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

    monkeypatch.setattr(web_app_module, "ImageService", FakeImageService)

    try:
        web_app_module.refresh_active_image()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/image/refresh-active", "POST"), exc))

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

    monkeypatch.setattr(web_app_module, "ImageService", FakeImageService)

    try:
        web_app_module.refresh_active_image()
        raise AssertionError("Expected FakePermissionDenied")
    except FakePermissionDenied as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/image/refresh-active", "POST"), exc))

    assert response.status_code == 400
    assert response.media_type == "application/problem+json"
    assert b"Content violates usage guidelines." in response.body


def test_revert_active_image_calls_character_image_service(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    calls: list[str] = []

    class FakeImageService:
        def revert(self) -> None:
            calls.append("revert")

    monkeypatch.setattr(web_app_module, "ImageService", FakeImageService)

    response = web_app_module.revert_active_image()

    assert response == {}
    assert calls == ["revert"]


def test_revert_active_image_returns_500_on_internal_runtime_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeImageService:
        def revert(self) -> None:
            raise RuntimeError("revert_failed")

    monkeypatch.setattr(web_app_module, "ImageService", FakeImageService)

    try:
        web_app_module.revert_active_image()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/image/revert-active", "POST"), exc))

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

    monkeypatch.setattr(web_app_module, "ImageService", FakeImageService)

    payload = web_app_module.delete_active_image()

    assert calls == ["delete_current"]
    assert payload["npc_id"] == "vika"
    assert payload["scene_id"] == "office"


def test_delete_active_image_returns_500_on_internal_runtime_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeImageService:
        def delete_current(self) -> None:
            raise RuntimeError("delete_failed")

    monkeypatch.setattr(web_app_module, "ImageService", FakeImageService)

    try:
        web_app_module.delete_active_image()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/image/delete-active", "DELETE"), exc))

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

    monkeypatch.setattr(web_app_module, "StreamingResponse", FakeStreamingResponse)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", fake_stream_prompt)
    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    response = web_app_module.chat_stream(web_app_module.ChatRequest(message="Startbild bitte"))

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

    monkeypatch.setattr(web_app_module, "StreamingResponse", FakeStreamingResponse)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", fake_stream_prompt)
    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    response = web_app_module.chat_stream(web_app_module.ChatRequest(message="Stream bitte"))

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

    monkeypatch.setattr(web_app_module, "StreamingResponse", FakeStreamingResponse)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", fake_stream_prompt)
    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    response = web_app_module.chat_stream(web_app_module.ChatRequest(message="Fehler bitte"))

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

    monkeypatch.setattr(web_app_module, "StreamingResponse", FakeStreamingResponse)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", fake_stream_prompt)

    response = web_app_module.chat_stream(web_app_module.ChatRequest(message="Fehler bitte"))

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

    monkeypatch.setattr(web_app_module, "StreamingResponse", FakeStreamingResponse)
    monkeypatch.setattr(web_app_module.client, "stream_prompt", fake_stream_prompt)

    response = web_app_module.chat_stream(web_app_module.ChatRequest(message="Teilantwort bitte"))

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

    monkeypatch.setattr(web_app_module, "StreamingResponse", FakeStreamingResponse)
    monkeypatch.setattr(web_app_module, "storage", FailingStorage())
    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    response = web_app_module.chat_stream(web_app_module.ChatRequest(message="Speichern bitte"))

    assert response.status_code == 200
    assert _read_stream_events(response) == [
        {"type": "chunk", "delta": "Antwort"},
        {"type": "chunk", "delta": " vom Web"},
        {"type": "error", "detail": "Interner Serverfehler."},
    ]
    assert calls == []


def test_update_user_profile_persists_active_runtime_profile_and_returns_it(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    scene_profile = config.DATA_NPC_DIR / "vika" / "office" / "user_profile.md"
    (config.NPC_DIR / "user_profile.md").write_text("default", encoding="utf-8")

    payload = web_app_module.update_user_profile(web_app_module.UserProfileRequest(content="global-profile"))

    assert scene_profile.read_text(encoding="utf-8") == "global-profile"
    assert payload["user_profile"] == "global-profile"


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


def test_web_lifespan_reuses_single_scheduler_instance(monkeypatch):
    events: list[str] = []

    class FakeScheduler:
        def __init__(self) -> None:
            events.append("init")

        def start(self) -> None:
            events.append("start")

        def stop(self) -> None:
            events.append("stop")

    monkeypatch.setattr(web_app_module, "_scheduler", None)
    monkeypatch.setattr(web_app_module, "Scheduler", FakeScheduler)

    async def run_lifespan():
        async with web_app_module._lifespan(web_app_module.app):
            events.append("inside")

    _run_async(run_lifespan())
    _run_async(run_lifespan())
    assert events == ["init", "start", "inside", "stop", "start", "inside", "stop"]


def test_create_scene_calls_scene_service(tmp_path, monkeypatch):
    import engine.web.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    created_scenes: list[str] = []
    created_npc_scenes: list[tuple[str, str]] = []

    def fake_scene_create(self, short_description: str):
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

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes/create",
            json={
                "scene_description": "Ein neues Café",
            }
        )

    assert response.status_code == 200
    assert created_scenes == ["Ein neues Café"]
    assert created_npc_scenes == [("Ein neues Café", "test_scene")]
    assert scheduler_calls == [("image", "test_scene")]
    assert storage.session.scene_id == "test_scene"


def test_create_scene_uses_same_description_for_scene_and_npc_scene(tmp_path, monkeypatch):
    import engine.web.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    created_scenes: list[str] = []
    created_npc_scenes: list[str] = []

    def fake_scene_create(self, short_description: str):
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

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes/create",
            json={
                "scene_description": "Ein neues Café",
            }
        )

    assert response.status_code == 200
    assert created_scenes == ["Ein neues Café"]
    assert created_npc_scenes == ["Ein neues Café"]


def test_create_scene_can_create_only_scene(tmp_path, monkeypatch):
    import engine.web.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\nimage_autogenerate: false\n", encoding="utf-8")

    created_scenes: list[str] = []
    created_npc_scenes: list[str] = []

    def fake_scene_create(self, short_description: str):
        created_scenes.append(short_description)
        scene_dir = tmp_path / ".overrides" / "scenes" / "test_scene"
        scene_dir.mkdir(parents=True, exist_ok=True)
        return scene_dir

    def fake_npc_scene_create(self, short_description: str):
        created_npc_scenes.append(short_description)

    monkeypatch.setattr(SceneService, "create_override", fake_scene_create)
    monkeypatch.setattr(NpcSceneService, "create_override", fake_npc_scene_create)

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes/create",
            json={"scene_description": "Ein neues Café", "create_scene": True, "create_npc_context": False},
        )

    assert response.status_code == 200
    assert created_scenes == ["Ein neues Café"]
    assert created_npc_scenes == []
    assert storage.session.scene_id == "test_scene"


def test_create_scene_can_create_only_npc_context(tmp_path, monkeypatch):
    import engine.web.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\nimage_autogenerate: false\n", encoding="utf-8")

    created_scenes: list[str] = []
    created_npc_scenes: list[tuple[str, str]] = []

    def fake_scene_create(self, short_description: str):
        created_scenes.append(short_description)
        return tmp_path / ".overrides" / "scenes" / "test_scene"

    def fake_npc_scene_create(self, short_description: str):
        created_npc_scenes.append((short_description, storage.session.scene_id))

    monkeypatch.setattr(SceneService, "create_override", fake_scene_create)
    monkeypatch.setattr(NpcSceneService, "create_override", fake_npc_scene_create)

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes/create",
            json={"scene_description": "NPC sitzt am Fenster", "create_scene": False, "create_npc_context": True},
        )

    assert response.status_code == 200
    assert created_scenes == []
    assert created_npc_scenes == [("NPC sitzt am Fenster", "cafe")]
    assert storage.session.scene_id == "cafe"


def test_create_scene_does_not_enqueue_image_job_when_autogenerate_is_disabled(tmp_path, monkeypatch):
    import engine.web.app as web_app_module
    from engine.services.npc_scene_service import NpcSceneService
    from engine.services.scene_service import SceneService

    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")
    storage.session.image_autogenerate = False

    def fake_scene_create(self, _short_description: str):
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

    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes/create",
            json={
                "scene_description": "Ein neues Café",
            }
        )

    assert response.status_code == 200
    assert scheduler_calls == []


def test_create_scene_rejects_empty_scene_description(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    class FakeScheduler:
        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    import engine.web.app as web_app_module
    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes/create",
            json={
                "scene_description": "   ",
            }
        )

    assert response.status_code == 400
    assert "darf nicht leer sein" in response.json()["detail"].lower()


def test_create_scene_rejects_missing_create_option(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    import engine.web.app as web_app_module

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/scenes/create",
            json={"scene_description": "Ein neues Café", "create_scene": False, "create_npc_context": False},
        )

    assert response.status_code == 400
    assert "mindestens eine" in response.json()["detail"].lower()


def test_create_npc_calls_npc_service_and_selects_new_npc(tmp_path, monkeypatch):
    import engine.web.app as web_app_module
    from engine.services.npc_service import NpcService

    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    created_npcs: list[str] = []

    def fake_npc_create(self, character_description: str):
        created_npcs.append(character_description)
        npc_dir = tmp_path / ".overrides" / "npcs" / "alex"
        npc_dir.mkdir(parents=True, exist_ok=True)
        (npc_dir / "character.yaml").write_text("name: Alex\n", encoding="utf-8")
        (npc_dir / "description.md").write_text("# Alex\n", encoding="utf-8")
        (npc_dir / "state.md").write_text("---\ntrust: 0\n---\n", encoding="utf-8")
        (npc_dir / "img.png").write_bytes(b"test-image-data")
        return npc_dir

    class FakeScheduler:
        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    monkeypatch.setattr(NpcService, "create_override", fake_npc_create)
    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/npcs/create",
            json={
                "character_description": "Alex, 28, arbeitet als Koch.",
            }
        )

    assert response.status_code == 200
    assert created_npcs == ["Alex, 28, arbeitet als Koch."]
    assert response.json()["npc_id"] == "alex"
    assert storage.session.npc_id == "alex"


def test_create_npc_rejects_empty_character_description(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")

    class FakeScheduler:
        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    import engine.web.app as web_app_module
    monkeypatch.setattr(web_app_module, "_get_scheduler", lambda: FakeScheduler())

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/npcs/create",
            json={
                "character_description": "   ",
            }
        )

    assert response.status_code == 400
    assert "darf nicht leer sein" in response.json()["detail"].lower()
