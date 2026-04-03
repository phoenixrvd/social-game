from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, cast

import pytest

import engine.updater.updater as abstract_updater_module
from engine.models import Npc, Scene, ShortMemoryMessage
import engine.updater.ltm_updater as ltm_updater_module
from engine.updater.ltm_updater import LtmUpdater
from tests.fakes import FakeLogger


class FakeNpcStore:
    def __init__(self, ltm: str = "", stm: list[ShortMemoryMessage] | None = None) -> None:
        self._ltm = ltm
        self._stm: list[ShortMemoryMessage] = list(stm or [])

    def load(self) -> Npc:
        return Npc(
            npc_id="vika",
            description="desc",
            system_prompt="sys",
            state="mood: neutral",
            character={"name": "Vika"},
            ltm=self._ltm,
            scene=Scene(scene_id="default", description="Szene"),
            stm=list(self._stm),
        )

    def save_ltm(self, ltm: str) -> None:
        self._ltm = ltm

    def remove_stm_by_ids(self, npc_id: str, scene_id: str, message_ids: Iterable[str]) -> None:
        assert npc_id == "vika"
        assert scene_id == "default"
        remove_set = set(message_ids)
        self._stm = [msg for msg in self._stm if msg.id not in remove_set]


@pytest.fixture(autouse=True)
def _mock_session_store(monkeypatch):
    def fake_load_text(path):
        if path == ltm_updater_module.config.PROJECT_ROOT / "prompts" / "ltm_summary.md":
            return """# Role: Long-Term-Memory Generator

## Bisherige Long-Term-Memory
{{LONG_TERM_MEMORY}}

## Neue Short-Memory-Nachrichten
{{SHORT_TERM_MEMORY}}
"""
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(ltm_updater_module, "load_text", fake_load_text)
    monkeypatch.setattr(ltm_updater_module, "run_prompt", lambda _prompt, model: "updated ltm")


def _build_updater(monkeypatch, npc_store: FakeNpcStore, tmp_path: Path) -> Any:
    monkeypatch.setattr(ltm_updater_module, "NpcStore", lambda: npc_store)
    monkeypatch.setattr(abstract_updater_module.config, "DATA_NPC_DIR", tmp_path / "npcs")
    return cast(Any, LtmUpdater())


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
        ltm_updater_module,
        "run_prompt",
        lambda _prompt, model: (_ for _ in ()).throw(AssertionError("LLM darf ohne batch nicht aufgerufen werden")),
    )
    updater = _build_updater(monkeypatch, npc_store, tmp_path)

    updater.schedule()

    assert npc_store.load().ltm == ""
    assert len(npc_store._stm) == 1


def test_schedule_with_batch_and_messages_triggers_update(monkeypatch, tmp_path):
    stm = _messages(
        ltm_updater_module.config.UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP
        + ltm_updater_module.config.UPDATER_LTM_BATCH_SIZE_THRESHOLD
        + 1,
        minutes_ago=0,
    )
    npc_store = FakeNpcStore(stm=stm)
    fake_logger = FakeLogger()

    captured_prompt: dict[str, Any] = {"value": None}

    def fake_summarizer(prompt: str) -> str:
        captured_prompt["value"] = prompt
        assert "msg-0" in prompt
        assert "msg-1" in prompt
        return "persisted ltm"

    monkeypatch.setattr(ltm_updater_module, "run_prompt", lambda prompt, model: fake_summarizer(prompt))
    monkeypatch.setattr(ltm_updater_module, "LOGGER", fake_logger)
    updater = _build_updater(monkeypatch, npc_store, tmp_path)

    updater.schedule()

    last_check_path = Path(tmp_path) / "npcs" / "vika" / "default" / "orchestrator" / "ltm_updater_last_check.txt"

    assert npc_store.load().ltm == "persisted ltm"
    assert len(npc_store._stm) == ltm_updater_module.config.UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP
    assert last_check_path.exists() is True
    assert captured_prompt["value"] is not None
    assert "## Bisherige Long-Term-Memory\n(leer)" in captured_prompt["value"]
    assert "## Neue Short-Memory-Nachrichten\nU: msg-0" in captured_prompt["value"]
    assert any(message.get("event") == "updater_active" and message.get("updater") == "ltm" and message.get("active") is True and message.get("prompt_start") is True for message in fake_logger.messages)
    assert any(message.get("event") == "updater_completed" and message.get("updater") == "ltm" for message in fake_logger.messages)


def test_schedule_without_new_messages_does_not_trigger(monkeypatch, tmp_path):
    stm = _messages(ltm_updater_module.config.UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP + 2, minutes_ago=120)
    npc_store = FakeNpcStore(ltm="x" * 9000, stm=stm)

    monkeypatch.setattr(
        ltm_updater_module,
        "run_prompt",
        lambda _prompt, model: (_ for _ in ()).throw(AssertionError("LLM darf ohne neue messages nicht aufgerufen werden")),
    )
    updater = _build_updater(monkeypatch, npc_store, tmp_path)

    last_check_path = Path(tmp_path) / "npcs" / "vika" / "default" / "orchestrator" / "ltm_updater_last_check.txt"
    last_check_path.parent.mkdir(parents=True, exist_ok=True)
    last_check_path.write_text(datetime.now(UTC).isoformat(), encoding="utf-8")

    updater.schedule()

    assert npc_store.load().ltm == "x" * 9000


def test_schedule_with_first_eligible_batch_triggers_immediately(monkeypatch, tmp_path):
    stm = _messages(
        ltm_updater_module.config.UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP
        + ltm_updater_module.config.UPDATER_LTM_BATCH_SIZE_THRESHOLD
        + 1,
        minutes_ago=0,
    )
    npc_store = FakeNpcStore(stm=stm)
    updater = _build_updater(monkeypatch, npc_store, tmp_path)

    monkeypatch.setattr(ltm_updater_module, "run_prompt", lambda _prompt, model: "fresh ltm")

    updater.schedule()

    assert npc_store.load().ltm == "fresh ltm"
    assert len(npc_store._stm) == ltm_updater_module.config.UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP
