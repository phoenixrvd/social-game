from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import engine.updater.scene_updater as scene_updater_module
import engine.updater.updater as abstract_updater_module
from engine.models import Npc, Scene, ShortMemoryMessage
from engine.updater.scene_updater import SceneUpdater


class FakeLogger:
    def __init__(self) -> None:
        self.messages: list[Any] = []

    def info(self, message: object, *args) -> None:
        if isinstance(message, str) and args:
            self.messages.append(message % args)
            return

        self.messages.append(message)


class FakeNpcStore:
    def __init__(self, npc: Npc) -> None:
        self._npc = npc
        self.saved_scene = False

    def load(self) -> Npc:
        return replace(self._npc)

    def save_scene(self, npc_id: str, scene_id: str, scene: str) -> None:
        assert npc_id == self._npc.npc_id
        assert scene_id == self._npc.scene.scene_id
        self._npc = replace(self._npc, scene=Scene(scene_id=scene_id, description=scene))
        self.saved_scene = True


@pytest.fixture(autouse=True)
def _mock_prompts(monkeypatch):
    def fake_load_text(path):
        if path == scene_updater_module.SCENE_PROMPT_PATH:
            return """# Role: Scene State Updater

## Aktuelle Szenendaten
{{SCENE_DATA}}

## Short-Term-Memory
{{SHORT_TERM_MEMORY}}

## Long-Term-Memory
{{LONG_TERM_MEMORY}}
"""
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(scene_updater_module, "load_text", fake_load_text)


def _npc(stm: list[ShortMemoryMessage] | None = None) -> Npc:
    return Npc(
        npc_id="vika",
        description="desc",
        system_prompt="sys",
        state="mood: neutral",
        character={"name": "Vika"},
        ltm="",
        scene=Scene(scene_id="default", description="office"),
        stm=stm or [],
    )


def _build_updater(monkeypatch, npc_store: FakeNpcStore, tmp_path) -> SceneUpdater:
    monkeypatch.setattr(scene_updater_module, "NpcStore", lambda: npc_store)
    monkeypatch.setattr(abstract_updater_module.config, "DATA_NPC_DIR", tmp_path / "npcs")
    return SceneUpdater()


def test_schedule_updates_scene_when_active(monkeypatch, tmp_path):
    class FakeImageUpdater:
        def __init__(self) -> None:
            self.emitted = False

        def emit_update(self) -> None:
            self.emitted = True

    fake_logger = FakeLogger()
    npc_store = FakeNpcStore(
        _npc(
            stm=[
                ShortMemoryMessage(
                    id="1",
                    timestamp_utc=datetime.now(UTC).isoformat(),
                    role="user",
                    content="Wir gehen ins Cafe",
                )
            ]
        )
    )
    updater = _build_updater(monkeypatch, npc_store, tmp_path)
    updater.image_updater = FakeImageUpdater()

    captured_prompt: list[str] = []

    def fake_run_prompt_small(prompt: str) -> str:
        captured_prompt.append(prompt)
        return "cafe"

    monkeypatch.setattr(scene_updater_module, "LOGGER", fake_logger)
    monkeypatch.setattr(scene_updater_module, "run_prompt_small", fake_run_prompt_small)

    updater.schedule()

    assert npc_store.saved_scene is True
    assert npc_store.load().scene.description == "cafe"
    assert updater.image_updater.emitted is True
    assert captured_prompt
    assert "## Aktuelle Szenendaten\noffice" in captured_prompt[0]
    assert "## Short-Term-Memory\nU: Wir gehen ins Cafe" in captured_prompt[0]
    assert "## Long-Term-Memory\n(leer)" in captured_prompt[0]
    assert any(message.get("event") == "updater_active" and message.get("updater") == "scene" and message.get("active") is True and message.get("prompt_start") is True for message in fake_logger.messages)


def test_schedule_is_noop_without_stm(monkeypatch, tmp_path):
    class FakeImageUpdater:
        def __init__(self) -> None:
            self.emitted = False

        def emit_update(self) -> None:
            self.emitted = True

    npc_store = FakeNpcStore(_npc(stm=[]))
    updater = _build_updater(monkeypatch, npc_store, tmp_path)
    updater.image_updater = FakeImageUpdater()

    monkeypatch.setattr(
        scene_updater_module,
        "run_prompt_small",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("LLM must not run")),
    )

    updater.schedule()

    assert npc_store.saved_scene is False
    assert updater.image_updater.emitted is False


def test_schedule_is_noop_without_new_messages_after_last_check(monkeypatch, tmp_path):
    class FakeImageUpdater:
        def __init__(self) -> None:
            self.emitted = False

        def emit_update(self) -> None:
            self.emitted = True

    old_timestamp = datetime(2026, 1, 1, tzinfo=UTC).isoformat()
    npc_store = FakeNpcStore(
        _npc(
            stm=[
                ShortMemoryMessage(
                    id="1",
                    timestamp_utc=old_timestamp,
                    role="user",
                    content="Wir gehen ins Cafe",
                )
            ]
        )
    )
    updater = _build_updater(monkeypatch, npc_store, tmp_path)
    updater.image_updater = FakeImageUpdater()

    last_check_path = Path(tmp_path) / "npcs" / "vika" / "default" / "orchestrator" / "scene_updater_last_check.txt"
    last_check_path.parent.mkdir(parents=True, exist_ok=True)
    last_check_path.write_text(old_timestamp, encoding="utf-8")

    monkeypatch.setattr(
        scene_updater_module,
        "run_prompt_small",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("LLM must not run")),
    )

    updater.schedule()

    assert npc_store.saved_scene is False
    assert updater.image_updater.emitted is False

