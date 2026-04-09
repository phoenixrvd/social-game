import asyncio
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException
from PIL import Image

import engine.web.app as web_app_module
from engine.models import Npc, Scene, Session, ShortMemoryMessage


def _make_test_png(path: Path) -> Path:
    img = Image.new("RGB", (4, 4), color=(80, 120, 160))
    img.save(path, format="PNG")
    return path


def _build_npc(npc_id: str, scene_id: str, messages: list[ShortMemoryMessage]) -> Npc:
    return Npc(
        npc_id=npc_id,
        description=f"Charakterbeschreibung {npc_id}",
        system_prompt="Bleib in Character",
        state="mood: neutral",
        ltm="kennt den Spieler",
        scene=Scene(scene_id=scene_id, description=f"Szene {scene_id}"),
        character={"name": npc_id.title()},
        img_current=Path(__file__),
        stm=messages,
    )


class FakeSessionStore:
    saved_calls: list[tuple[str | None, str | None]] = []
    current = Session(npc_id="vika", scene_id="office")

    def load(self) -> Session:
        return type(self).current

    def save(self, *, npc: str | None = None, scene: str | None = None) -> Session:
        type(self).saved_calls.append((npc, scene))
        type(self).current = Session(
            npc_id=npc or type(self).current.npc_id,
            scene_id=scene or type(self).current.scene_id,
        )
        return type(self).current


class FakeNpcStore:
    def __init__(self) -> None:
        self.appended_turns: list[tuple[str, str]] = []
        self._message_counter = 2
        self._current_npc = _build_npc(
            npc_id=FakeSessionStore.current.npc_id,
            scene_id=FakeSessionStore.current.scene_id,
            messages=[
                ShortMemoryMessage(
                    id="m1",
                    timestamp_utc="2026-03-22T10:00:00+00:00",
                    role="user",
                    content="Hi",
                ),
                ShortMemoryMessage(
                    id="m2",
                    timestamp_utc="2026-03-22T10:01:00+00:00",
                    role="assistant",
                    content="Hallo.",
                ),
            ],
        )

    def load(self) -> Npc:
        session = FakeSessionStore.current
        current = replace(
            self._current_npc,
            npc_id=session.npc_id,
            scene=Scene(scene_id=session.scene_id, description=f"Szene {session.scene_id}"),
            character={"name": session.npc_id.title()},
        )
        return replace(current, stm=list(current.stm), character=dict(current.character))

    def append_stm_turn(self, user_content: str, assistant_content: str) -> list[ShortMemoryMessage]:
        self.appended_turns.append((user_content, assistant_content))
        self._message_counter += 1
        user_message = ShortMemoryMessage(
            id=f"m{self._message_counter}",
            timestamp_utc="2026-03-22T10:02:00+00:00",
            role="user",
            content=user_content,
        )
        self._message_counter += 1
        assistant_message = ShortMemoryMessage(
            id=f"m{self._message_counter}",
            timestamp_utc="2026-03-22T10:03:00+00:00",
            role="assistant",
            content=assistant_content,
        )
        self._current_npc.stm.extend([user_message, assistant_message])
        return [user_message, assistant_message]

class FakeNpcTurnService:
    def __init__(self) -> None:
        self.npc_store = fake_npc_store

    def build_turn_messages(self):
        return [{"role": "system", "content": "stub"}]

    def build_user_message(self, player_input: str):
        return {"role": "user", "content": player_input}


fake_npc_store = FakeNpcStore()


def _setup_web_app(
    tmp_path,
    monkeypatch,
    *,
    web_debug: bool = False,
) -> None:
    npcs_dir = tmp_path / "npcs"
    scenes_dir = tmp_path / "scenes"
    data_npcs_dir = tmp_path / ".data" / "npcs"
    for npc_id, label in (("vika", "Vika"), ("mira", "Mira")):
        npc_dir = npcs_dir / npc_id
        npc_dir.mkdir(parents=True)
        (npc_dir / "character.yaml").write_text(f"name: {label}\n", encoding="utf-8")
    for scene_id, heading in (("office", "# Office"), ("cafe", "# Cafe")):
        scene_dir = scenes_dir / scene_id
        scene_dir.mkdir(parents=True)
        (scene_dir / "scene.md").write_text(heading, encoding="utf-8")

    (data_npcs_dir / "vika").mkdir(parents=True)
    (data_npcs_dir / "vika" / "stm.jsonl").write_text('{"role":"user","content":"x"}\n', encoding="utf-8")

    test_img_path = _make_test_png(tmp_path / "test_img.png")

    FakeSessionStore.saved_calls = []
    FakeSessionStore.current = Session(npc_id="vika", scene_id="office")
    fake_npc_store.appended_turns = []
    fake_npc_store._message_counter = 2
    fake_npc_store._current_npc = _build_npc(
        npc_id="vika",
        scene_id="office",
        messages=[
            ShortMemoryMessage(
                id="m1",
                timestamp_utc="2026-03-22T10:00:00+00:00",
                role="user",
                content="Hi",
            ),
            ShortMemoryMessage(
                id="m2",
                timestamp_utc="2026-03-22T10:01:00+00:00",
                role="assistant",
                content="Hallo.",
            ),
        ],
    )
    fake_npc_store._current_npc = replace(fake_npc_store._current_npc, img_current=test_img_path)

    monkeypatch.setattr(web_app_module.config, "NPC_DIR", npcs_dir)
    monkeypatch.setattr(web_app_module.config, "SCENE_DIR", scenes_dir)
    monkeypatch.setattr(web_app_module.config, "DATA_NPC_DIR", data_npcs_dir)
    monkeypatch.setattr(web_app_module.config, "WEB_DEBUG", web_debug)
    monkeypatch.setattr(web_app_module, "SessionStore", FakeSessionStore)
    monkeypatch.setattr(web_app_module, "NpcStore", lambda: fake_npc_store)
    monkeypatch.setattr(web_app_module, "NpcTurnService", FakeNpcTurnService)
    monkeypatch.setattr(web_app_module, "stream_prompt", lambda turn_messages: iter(["Antwort", " vom Web"]))
    web_app_module.app.state.watch_scheduler = None

def _request(path: str, method: str = "GET"):
    return SimpleNamespace(url=SimpleNamespace(path=path), method=method)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


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
    assert "object-src 'none'" in csp, "CSP fehlt object-src 'none'"
    assert "frame-ancestors 'none'" in csp, "CSP fehlt frame-ancestors"
    assert "require-trusted-types-for 'script'" in csp, "CSP fehlt Trusted Types"
    assert "trusted-types sg" in csp, "CSP fehlt trusted-types Policy-Name"

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
    payload = web_app_module.get_state()
    assert payload["npc_id"] == "vika"
    assert payload["npc_name"] == "Vika"
    assert payload["character_description"] == "Charakterbeschreibung vika"
    assert payload["character_data"] == {"name": "Vika"}
    assert payload["scene_id"] == "office"
    assert payload["ltm"] == "kennt den Spieler"
    assert payload["image_url"] == "/api/image/current"
    assert payload["messages"][0]["content"] == "Hi"
    assert payload["npcs"] == [{"id": "mira", "label": "Mira"}, {"id": "vika", "label": "Vika"}]
    assert payload["scenes"] == [{"id": "cafe", "label": "Cafe"}, {"id": "office", "label": "Office"}]


def test_get_state_returns_context_message_when_history_is_empty(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    fake_npc_store._current_npc = _build_npc(
        npc_id="vika",
        scene_id="office",
        messages=[],
    )

    payload = web_app_module.get_state()
    assert len(payload["messages"]) == 3
    character_message = payload["messages"][0]
    scene_message = payload["messages"][1]
    ltm_message = payload["messages"][2]
    assert character_message["id"] == "context-character"
    assert scene_message["id"] == "context-scene"
    assert ltm_message["id"] == "context-ltm"
    assert character_message["role"] == "assistant"
    assert scene_message["role"] == "assistant"
    assert ltm_message["role"] == "assistant"
    assert character_message["content"] == ""
    assert scene_message["content"] == ""
    assert ltm_message["content"] == ""
    assert "Charakterbeschreibung vika" in character_message["html"]
    assert "Szene office" in scene_message["html"]
    assert "kennt den Spieler" in ltm_message["html"]


def test_get_state_prefers_real_messages_over_context_fallback(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    payload = web_app_module.get_state()
    assert len(payload["messages"]) == 2
    assert payload["messages"][0]["content"] == "Hi"
    assert payload["messages"][1]["content"] == "Hallo."


def test_get_state_returns_context_message_when_only_system_messages_exist(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    fake_npc_store._current_npc = _build_npc(
        npc_id="vika",
        scene_id="office",
        messages=[
            ShortMemoryMessage(
                id="m-system",
                timestamp_utc="2026-03-22T09:59:00+00:00",
                role="system",
                content="Interner Zustand",
            )
        ],
    )

    payload = web_app_module.get_state()
    assert len(payload["messages"]) == 3
    assert payload["messages"][0]["id"] == "context-character"
    assert payload["messages"][1]["id"] == "context-scene"
    assert payload["messages"][2]["id"] == "context-ltm"
    assert "Charakterbeschreibung vika" in payload["messages"][0]["html"]
    assert "Szene office" in payload["messages"][1]["html"]



def test_get_state_context_html_keeps_markdown_links_unescaped(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    fake_npc_store._current_npc = replace(
        fake_npc_store._current_npc,
        description="[link](javascript:alert('x'))",
        stm=[],
        scene=Scene(scene_id="office", description="Szene [ok](https://example.com)"),
    )

    payload = web_app_module.get_state()
    character_html = payload["messages"][0]["html"]
    assert "javascript:" in character_html


def test_get_state_context_html_renders_label_lists_as_html_lists(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    fake_npc_store._current_npc = replace(
        fake_npc_store._current_npc,
        description="Au\u00dfen:\n\n- direkt\n- offen",
        stm=[],
    )

    payload = web_app_module.get_state()
    character_html = payload["messages"][0]["html"]
    assert "<ul>" in character_html
    assert "<li>direkt</li>" in character_html
    assert "<li>offen</li>" in character_html


def test_update_session_persists_and_returns_new_state(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    payload = web_app_module.update_session(web_app_module.SessionRequest(npc_id="mira", scene_id="cafe"))
    assert FakeSessionStore.saved_calls == [("mira", "cafe")]
    assert payload["npc_id"] == "mira"
    assert payload["npc_name"] == "Mira"
    assert payload["scene_id"] == "cafe"


def test_update_session_requires_at_least_one_field(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    try:
        web_app_module.update_session(web_app_module.SessionRequest())
        raise AssertionError("Expected HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Mindestens npc_id oder scene_id muss gesetzt sein."


def test_reset_active_npc_runtime_data_deletes_directory(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    scene_data_dir = tmp_path / ".data" / "npcs" / "vika" / "office"
    scene_data_dir.mkdir(parents=True, exist_ok=True)
    assert scene_data_dir.exists()

    payload = web_app_module.reset_active_npc_runtime_data()

    assert not scene_data_dir.exists()
    assert payload["npc_id"] == "vika"
    assert payload["scene_id"] == "office"


def test_current_image_serves_active_npc_image(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    response = web_app_module.current_image()

    assert response.status_code == 200
    assert response.media_type == "image/webp"
    assert len(response.body) > 0


def test_current_image_returns_404_when_missing(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    fake_npc_store._current_npc = _build_npc(
        npc_id="vika",
        scene_id="office",
        messages=[],
    )
    fake_npc_store._current_npc.img_current = tmp_path / "missing.png"

    try:
        web_app_module.current_image()
        raise AssertionError("Expected HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 404
        assert "Kein NPC-Bild verfügbar." in exc.detail
        assert "npc_id='vika'" in exc.detail
        assert "scene_id='office'" in exc.detail


def test_refresh_active_image_triggers_emit_update_before_schedule(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    calls: list[str] = []

    class FakeImageUpdater:
        def emit_update(self) -> None:
            calls.append("emit_update")

        def schedule(self, force: bool = False) -> None:
            assert force is True
            calls.append("schedule")

    monkeypatch.setattr(web_app_module, "ImageUpdater", FakeImageUpdater)

    response = web_app_module.refresh_active_image()

    assert response == {}
    assert calls == ["emit_update", "schedule"]


def test_refresh_active_image_returns_500_on_schedule_error(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)

    class FakeImageUpdater:
        def emit_update(self) -> None:
            pass

        def schedule(self, force: bool = False) -> None:
            raise RuntimeError("generation_failed")

    monkeypatch.setattr(web_app_module, "ImageUpdater", FakeImageUpdater)

    try:
        web_app_module.refresh_active_image()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        response = _run_async(web_app_module._internal_error_handler(_request("/api/image/refresh-active", "POST"), exc))

    assert response.status_code == 500
    assert response.media_type == "application/problem+json"
    assert b"Interner Serverfehler." in response.body
    assert b"generation_failed" not in response.body


def test_chat_stream_emits_initial_image_update_when_generated_image_is_missing(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    calls: list[str] = []

    class FakeStreamingResponse:
        def __init__(self, content, media_type: str):
            self.status_code = 200
            self.media_type = media_type
            self.body_iterator = content

    class FakeImageUpdater:
        def emit_update_if_missing(self) -> None:
            calls.append("emit_update_if_missing")

    monkeypatch.setattr(web_app_module, "StreamingResponse", FakeStreamingResponse)
    monkeypatch.setattr(web_app_module, "ImageUpdater", FakeImageUpdater)

    response = web_app_module.chat_stream(web_app_module.ChatRequest(message="Startbild bitte"))

    assert response.status_code == 200
    assert list(response.body_iterator) == ["Antwort", " vom Web"]
    assert calls == ["emit_update_if_missing"]


def test_chat_stream_skips_initial_image_emit_when_generated_image_exists(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    calls: list[str] = []

    class FakeStreamingResponse:
        def __init__(self, content, media_type: str):
            self.status_code = 200
            self.media_type = media_type
            self.body_iterator = content

    class FakeImageUpdater:
        def emit_update_if_missing(self) -> None:
            calls.append("emit_update_if_missing")

    monkeypatch.setattr(web_app_module, "StreamingResponse", FakeStreamingResponse)
    monkeypatch.setattr(web_app_module, "ImageUpdater", FakeImageUpdater)

    response = web_app_module.chat_stream(web_app_module.ChatRequest(message="Noch eine Nachricht"))

    assert response.status_code == 200
    assert list(response.body_iterator) == ["Antwort", " vom Web"]
    assert calls == ["emit_update_if_missing"]


def test_chat_endpoint_is_not_available_anymore(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    assert all(getattr(route, "path", None) != "/api/chat" for route in web_app_module.app.routes)


def test_chat_stream_endpoint_streams_plain_text(tmp_path, monkeypatch):
    _setup_web_app(tmp_path, monkeypatch)
    captured: dict[str, object] = {}

    class FakeStreamingResponse:
        def __init__(self, content, media_type: str):
            self.status_code = 200
            self.media_type = media_type
            self.body_iterator = content

    def fake_stream_prompt(turn_messages):
        captured["turn_messages"] = turn_messages
        return iter(["Antwort", " vom Web"])

    monkeypatch.setattr(web_app_module, "StreamingResponse", FakeStreamingResponse)
    monkeypatch.setattr(web_app_module, "stream_prompt", fake_stream_prompt)

    response = web_app_module.chat_stream(web_app_module.ChatRequest(message="Stream bitte"))

    assert response.status_code == 200
    assert response.media_type == "text/plain; charset=utf-8"
    assert captured["turn_messages"] == [
        {"role": "system", "content": "stub"},
        {"role": "user", "content": "Stream bitte"},
    ]
    assert type(response.body_iterator).__name__ == "generator"


def test_web_lifecycle_starts_and_stops_watchers(monkeypatch):
    events: dict[str, object] = {}

    def fake_start_scheduler(*, scheduler=None, run_immediately=True):
        events["run_immediately"] = run_immediately
        events["scheduler_arg"] = scheduler
        return "SCHED", []

    def fake_stop_scheduler(scheduler):
        events["stopped"] = scheduler

    monkeypatch.setattr(web_app_module, "start_scheduler", fake_start_scheduler)
    monkeypatch.setattr(web_app_module, "stop_scheduler", fake_stop_scheduler)

    web_app_module.app.state.watch_scheduler = None
    web_app_module._start_watchers_for_web()
    assert events["run_immediately"] is True
    assert web_app_module.app.state.watch_scheduler == "SCHED"

    web_app_module._stop_watchers_for_web()
    assert events["stopped"] == "SCHED"
    assert web_app_module.app.state.watch_scheduler is None
