from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

import engine.services.scene_update_service as scene_update_service_module
import engine.storage as storage_module
import engine.updater.scene_updater as scene_updater_module
from engine.models import Npc, Scene, ShortMemoryMessage
from engine.updater.scene_updater import SceneUpdater


class FakeNpcStore:
    def __init__(self, npc: Npc) -> None:
        self._npc = npc
        self.saved_scene = False

    def load(self) -> Npc:
        return replace(self._npc)


class FakeSceneStorage:
    def __init__(self, npc_store: FakeNpcStore, prompt_text: str) -> None:
        self.scene = self._build_scene_view(npc_store)
        self.prompts = self._build_prompts(prompt_text)

    @staticmethod
    def _build_scene_view(npc_store: FakeNpcStore):
        class FakeSceneRuntime:
            def save(self, scene: str) -> None:
                npc_store._npc = replace(
                    npc_store._npc,
                    scene=Scene(scene_id=npc_store._npc.scene.scene_id, description=scene),
                )
                npc_store.saved_scene = True

        class FakeSceneView:
            scene_runtime = FakeSceneRuntime()

        return FakeSceneView()

    @staticmethod
    def _build_prompts(prompt_text: str):
        class FakePrompt:
            def get(self) -> str:
                return prompt_text

        class FakePrompts:
            scene_update = FakePrompt()

        return FakePrompts()


@pytest.fixture(autouse=True)
def _mock_prompts(monkeypatch):
    prompt_text = """# Role: Scene State Updater

## Aktuelle Szenendaten
{{SCENE_DATA}}

## Relevant Earlier ETM Episodes
{{CURRENT_ETM}}

## Short-Term-Memory
{{SHORT_TERM_MEMORY}}
"""
    monkeypatch.setattr(scene_update_service_module, "_TEST_SCENE_UPDATE_PROMPT", prompt_text, raising=False)


def _npc(stm: list[ShortMemoryMessage] | None = None) -> Npc:
    return Npc(
        npc_id="vika",
        description="desc",
        system_prompt="sys",
        state="mood: neutral",
        character={"name": "Vika"},
        relationship="",
        scene=Scene(scene_id="default", description="office"),
        stm=stm or [],
    )


def _build_updater(monkeypatch, npc_store: FakeNpcStore, tmp_path) -> SceneUpdater:
    monkeypatch.setattr(scene_updater_module, "NpcStore", lambda: npc_store)
    prompt_text = getattr(scene_update_service_module, "_TEST_SCENE_UPDATE_PROMPT")
    monkeypatch.setattr(scene_update_service_module, "storage", FakeSceneStorage(npc_store, prompt_text))
    monkeypatch.setattr(storage_module.config, "DATA_NPC_DIR", tmp_path / "npcs")
    return SceneUpdater()


def test_schedule_updates_scene_when_active(monkeypatch, tmp_path):
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
                    content="Wir gehen ins Cafe",
                )
            ]
        )
    )
    updater = _build_updater(monkeypatch, npc_store, tmp_path)
    updater.service.image_updater = FakeImageUpdater()

    captured_prompt: list[str] = []

    def fake_run_prompt(prompt: str) -> str:
        captured_prompt.append(prompt)
        return "cafe"

    monkeypatch.setattr(scene_update_service_module, "run_prompt_small", lambda prompt: fake_run_prompt(prompt))

    updater.schedule()

    assert npc_store.saved_scene is True
    assert npc_store.load().scene.description == "cafe"
    assert updater.service.image_updater.emitted is True
    assert captured_prompt
    assert "## Aktuelle Szenendaten\noffice" in captured_prompt[0]
    assert "## Short-Term-Memory\nU: Wir gehen ins Cafe" in captured_prompt[0]
    assert "## Relevant Earlier ETM Episodes" in captured_prompt[0]


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
        scene_update_service_module,
        "run_prompt_small",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("LLM must not run")),
    )

    updater.schedule()

    assert npc_store.saved_scene is False
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
                    content="Wir gehen ins Cafe",
                )
            ]
        )
    )
    updater = _build_updater(monkeypatch, npc_store, tmp_path)
    updater.service.image_updater = FakeImageUpdater()

    last_check_path = Path(tmp_path) / "npcs" / "vika" / "default" / "orchestrator" / "scene_updater_last_check.txt"
    last_check_path.parent.mkdir(parents=True, exist_ok=True)
    last_check_path.write_text(old_timestamp, encoding="utf-8")

    monkeypatch.setattr(
        scene_update_service_module,
        "run_prompt_small",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("LLM must not run")),
    )

    updater.schedule()

    assert npc_store.saved_scene is False
    assert updater.service.image_updater.emitted is False
