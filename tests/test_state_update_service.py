from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

import engine.services.state_update_service as state_update_service_module
import engine.storage as storage_module
import engine.updater.state_updater as state_updater_module
from engine.models import Npc, Scene, ShortMemoryMessage
from engine.updater.state_updater import StateUpdater


class FakeNpcStore:
    def __init__(self, npc: Npc) -> None:
        self._npc = npc
        self.saved = False

    def load(self) -> Npc:
        return replace(self._npc)


class FakeStateStorage:
    def __init__(self, npc_store: FakeNpcStore, prompt_text: str) -> None:
        self.npc = self._build_npc_view(npc_store)
        self.prompts = self._build_prompts(prompt_text)

    @staticmethod
    def _build_npc_view(npc_store: FakeNpcStore):
        class FakeStateRuntime:
            def save(self, state: str) -> None:
                npc_store._npc = replace(npc_store._npc, state=state)
                npc_store.saved = True

        class FakeNpcView:
            state_runtime = FakeStateRuntime()

        return FakeNpcView()

    @staticmethod
    def _build_prompts(prompt_text: str):
        class FakePrompt:
            def get(self) -> str:
                return prompt_text

        class FakePrompts:
            state_update = FakePrompt()

        return FakePrompts()


@pytest.fixture(autouse=True)
def _mock_prompts(monkeypatch):
    prompt_text = """# Role: NPC State Updater

## Current State
{{CURRENT_STATE}}

## Short-Term-Memory
{{SHORT_TERM_MEMORY}}

## Relevant Earlier ETM Episodes
{{CURRENT_ETM}}
"""
    monkeypatch.setattr(state_update_service_module, "_TEST_STATE_UPDATE_PROMPT", prompt_text, raising=False)


def _npc(stm: list[ShortMemoryMessage] | None = None) -> Npc:
    return Npc(
        npc_id="vika",
        description="desc",
        system_prompt="sys",
        state="mood: neutral",
        character={"name": "Vika"},
        relationship="freundlich",
        scene=Scene(scene_id="default", description="Szene"),
        stm=stm or [],
    )


def _build_updater(monkeypatch, npc_store: FakeNpcStore, tmp_path) -> StateUpdater:
    monkeypatch.setattr(state_updater_module, "NpcStore", lambda: npc_store)
    prompt_text = getattr(state_update_service_module, "_TEST_STATE_UPDATE_PROMPT")
    monkeypatch.setattr(state_update_service_module, "storage", FakeStateStorage(npc_store, prompt_text))
    monkeypatch.setattr(storage_module.config, "DATA_NPC_DIR", tmp_path / "npcs")
    return StateUpdater()


def test_schedule_updates_state_when_active(monkeypatch, tmp_path):
    class FakeImageUpdater:
        def __init__(self) -> None:
            self.emitted = False

        def emit_update(self) -> None:
            self.emitted = True

    npc_store = FakeNpcStore(
        _npc(
            stm=[
                ShortMemoryMessage(
                    id="1",
                    timestamp_utc=datetime.now(UTC).isoformat(),
                    role="user",
                    content="Hallo",
                )
            ]
        )
    )
    updater = _build_updater(monkeypatch, npc_store, tmp_path)
    updater.service.image_updater = FakeImageUpdater()

    captured_prompt: dict[str, str | None] = {"value": None}

    def fake_run_prompt(prompt: str) -> str:
        captured_prompt["value"] = prompt
        return "mood: happy"

    monkeypatch.setattr(state_update_service_module, "run_prompt", lambda prompt, model: fake_run_prompt(prompt))

    updater.schedule()

    assert npc_store.saved is True
    assert npc_store.load().state == "mood: happy"
    assert updater.service.image_updater.emitted is True
    assert captured_prompt["value"] is not None
    assert "## Current State\nmood: neutral" in captured_prompt["value"]
    assert "## Short-Term-Memory\nU: Hallo" in captured_prompt["value"]
    assert "## Relevant Earlier ETM Episodes" in captured_prompt["value"]


def test_schedule_is_noop_without_stm(monkeypatch, tmp_path):
    class FakeImageUpdater:
        def __init__(self) -> None:
            self.emitted = False

        def emit_update(self) -> None:
            self.emitted = True

    npc_store = FakeNpcStore(_npc(stm=[]))
    updater = _build_updater(monkeypatch, npc_store, tmp_path)
    updater.service.image_updater = FakeImageUpdater()

    monkeypatch.setattr(
        state_update_service_module,
        "run_prompt",
        lambda _prompt, model: (_ for _ in ()).throw(AssertionError("LLM must not run")),
    )

    updater.schedule()

    assert npc_store.saved is False
    assert updater.service.image_updater.emitted is False


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
                    content="Hallo",
                )
            ]
        )
    )
    updater = _build_updater(monkeypatch, npc_store, tmp_path)
    updater.service.image_updater = FakeImageUpdater()

    last_check_path = Path(tmp_path) / "npcs" / "vika" / "default" / "orchestrator" / "state_updater_last_check.txt"
    last_check_path.parent.mkdir(parents=True, exist_ok=True)
    last_check_path.write_text(old_timestamp, encoding="utf-8")

    monkeypatch.setattr(
        state_update_service_module,
        "run_prompt",
        lambda _prompt, model: (_ for _ in ()).throw(AssertionError("LLM must not run")),
    )

    updater.schedule()

    assert npc_store.saved is False
    assert updater.service.image_updater.emitted is False
