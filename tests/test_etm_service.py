from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, cast

import pytest

import engine.services.etm_update_service as etm_update_service_module
import engine.storage as storage_module
import engine.updater.etm_updater as etm_updater_module
from engine.models import Npc, Scene, ShortMemoryMessage
from engine.updater.etm_updater import EtmUpdater


class FakeNpcStore:
    def __init__(self, relationship: str = "", stm: list[ShortMemoryMessage] | None = None) -> None:
        self._relationship = relationship
        self._stm: list[ShortMemoryMessage] = list(stm or [])

    def load(self) -> Npc:
        return Npc(
            npc_id="vika",
            description="desc",
            system_prompt="sys",
            state="mood: neutral",
            character={"name": "Vika"},
            relationship=self._relationship,
            scene=Scene(scene_id="default", description="Szene"),
            stm=list(self._stm),
        )

    def remove_stm_by_ids(self, message_ids: Iterable[str]) -> None:
        remove_set = set(message_ids)
        self._stm = [msg for msg in self._stm if msg.id not in remove_set]


class FakeEtmVectorStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.added: list[tuple[str, list[float], str]] = []

    def add(self, text: str, embedding: list[float], entry_id: str) -> None:
        self.added.append((text, embedding, entry_id))


_FAKE_EMBEDDING = [0.1, 0.2, 0.3]


@pytest.fixture(autouse=True)
def _patch_etm_updater(monkeypatch):
    monkeypatch.setattr(storage_module.config, "PROJECT_ROOT", Path("/tmp/test-project-root"))

    class FakePrompt:
        def get(self) -> str:
            return "{{SHORT_TERM_MEMORY}}"

    class FakePrompts:
        etm_update = FakePrompt()

    class FakeStorage:
        prompts = FakePrompts()
        npc = None

    monkeypatch.setattr(etm_update_service_module, "storage", FakeStorage())
    monkeypatch.setattr(etm_update_service_module, "run_prompt_small", lambda prompt: "updated episode")
    monkeypatch.setattr(etm_update_service_module, "embed_texts", lambda texts, **_: [_FAKE_EMBEDDING for _ in texts])
    monkeypatch.setattr(etm_update_service_module, "EtmVectorStore", FakeEtmVectorStore)


def _build_updater(monkeypatch, npc_store: FakeNpcStore, tmp_path: Path) -> Any:
    monkeypatch.setattr(etm_update_service_module, "NpcStore", lambda: npc_store)
    monkeypatch.setattr(storage_module.config, "DATA_NPC_DIR", tmp_path / "npcs")
    class FakeNpcView:
        etm_chroma = tmp_path / "npcs" / "vika" / "default" / "etm.chroma"

    etm_update_service_module.storage.npc = FakeNpcView()
    return cast(Any, EtmUpdater())


def _iso(minutes_ago: int) -> str:
    return (datetime.now(UTC) - timedelta(minutes=minutes_ago)).isoformat()


def _messages(count: int, *, minutes_ago: int = 120) -> list[ShortMemoryMessage]:
    return [
        ShortMemoryMessage(
            id=str(i),
            timestamp_utc=_iso(minutes_ago),
            role="user" if i % 2 == 0 else "assistant",
            content=f"msg-{i}",
        )
        for i in range(count)
    ]


def test_schedule_with_insufficient_batch_does_not_trigger(monkeypatch, tmp_path):
    npc_store = FakeNpcStore(stm=_messages(1, minutes_ago=0))

    monkeypatch.setattr(
        etm_update_service_module,
        "run_prompt_small",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("LLM darf ohne batch nicht aufgerufen werden")),
    )
    updater = _build_updater(monkeypatch, npc_store, tmp_path)

    updater.schedule()

    assert npc_store.load().relationship == ""
    assert len(npc_store._stm) == 1


def test_schedule_with_batch_and_messages_creates_etm_episode(monkeypatch, tmp_path):
    stm = _messages(
        etm_updater_module.config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP
        + etm_updater_module.config.UPDATER_ETM_BATCH_SIZE_THRESHOLD
        + 1,
        minutes_ago=0,
    )
    npc_store = FakeNpcStore(stm=stm)
    captured_stores: list[FakeEtmVectorStore] = []
    call_count = {"n": 0}

    def fake_run_prompt(prompt: str) -> str:
        call_count["n"] += 1
        assert "msg-0" in prompt
        assert "msg-1" in prompt
        assert "user:" in prompt
        assert "assistant:" in prompt
        assert "U:" not in prompt
        assert "A:" not in prompt
        return "episode from npc perspective"

    def fake_vector_store(path: Path) -> FakeEtmVectorStore:
        store = FakeEtmVectorStore(path)
        captured_stores.append(store)
        return store

    monkeypatch.setattr(etm_update_service_module, "run_prompt_small", fake_run_prompt)
    monkeypatch.setattr(etm_update_service_module, "EtmVectorStore", fake_vector_store)
    updater = _build_updater(monkeypatch, npc_store, tmp_path)

    updater.schedule()

    last_check_path = Path(tmp_path) / "npcs" / "vika" / "default" / "orchestrator" / "etm_updater_last_check.txt"

    assert npc_store.load().relationship == ""
    assert len(npc_store._stm) == etm_updater_module.config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP
    assert last_check_path.exists() is True
    assert call_count["n"] == 1
    assert len(captured_stores) == 1
    assert captured_stores[0].path == Path(tmp_path) / "npcs" / "vika" / "default" / "etm.chroma"
    assert captured_stores[0].added[0][0] == "episode from npc perspective"


def test_schedule_without_new_messages_does_not_trigger(monkeypatch, tmp_path):
    stm = _messages(etm_updater_module.config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP + 2, minutes_ago=120)
    npc_store = FakeNpcStore(relationship="x" * 9000, stm=stm)

    monkeypatch.setattr(
        etm_update_service_module,
        "run_prompt_small",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("LLM darf ohne neue messages nicht aufgerufen werden")),
    )
    updater = _build_updater(monkeypatch, npc_store, tmp_path)

    last_check_path = Path(tmp_path) / "npcs" / "vika" / "default" / "orchestrator" / "etm_updater_last_check.txt"
    last_check_path.parent.mkdir(parents=True, exist_ok=True)
    last_check_path.write_text(datetime.now(UTC).isoformat(), encoding="utf-8")

    updater.schedule()

    assert npc_store.load().relationship == "x" * 9000


def test_schedule_with_first_eligible_batch_triggers_immediately(monkeypatch, tmp_path):
    stm = _messages(
        etm_updater_module.config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP
        + etm_updater_module.config.UPDATER_ETM_BATCH_SIZE_THRESHOLD
        + 1,
        minutes_ago=0,
    )
    npc_store = FakeNpcStore(stm=stm)

    monkeypatch.setattr(etm_update_service_module, "run_prompt_small", lambda prompt: "fresh episode")
    updater = _build_updater(monkeypatch, npc_store, tmp_path)

    updater.schedule()

    assert npc_store.load().relationship == ""
    assert len(npc_store._stm) == etm_updater_module.config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP


def test_vector_store_receives_correct_embedding(monkeypatch, tmp_path):
    stm = _messages(
        etm_updater_module.config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP
        + etm_updater_module.config.UPDATER_ETM_BATCH_SIZE_THRESHOLD
        + 1,
        minutes_ago=0,
    )
    npc_store = FakeNpcStore(stm=stm)
    captured: list[FakeEtmVectorStore] = []
    custom_embedding = [0.9, 0.8, 0.7]

    monkeypatch.setattr(etm_update_service_module, "embed_texts", lambda texts, **_: [custom_embedding for _ in texts])
    monkeypatch.setattr(
        etm_update_service_module,
        "EtmVectorStore",
        lambda path: (captured.append(s := FakeEtmVectorStore(path)) or s),
    )
    updater = _build_updater(monkeypatch, npc_store, tmp_path)

    updater.schedule()

    assert len(captured) == 1
    assert captured[0].added[0][1] == custom_embedding
