from pathlib import Path
from types import SimpleNamespace
from typing import Literal, cast

import engine.services.npc_turn_service as npc_turn_service_module
from engine.services.npc_turn_service import NpcTurnService
from engine.storage.models import Message


class FakeStmView:
    def __init__(self, messages: list[Message] | None = None) -> None:
        self._messages = list(messages or [])

    def get(self) -> list[Message]:
        return list(self._messages)

    @property
    def text_short_latest(self) -> str:
        selected = self._messages[-npc_turn_service_module.config.STM_LATEST_MESSAGES:]
        if not selected:
            return "(keine Nachrichten)"
        return "\n".join(f"{m.role}: {m.content.strip()}" for m in selected)


def _build_npc(**overrides) -> SimpleNamespace:
    base = SimpleNamespace(
        npc_id="vika",
        description="Beschreibung",
        system_prompt="Bleib in Character",
        state="mood: neutral",
        relationship="Kennt den Spieler",
        scene=SimpleNamespace(scene_id="office", description="Im Buero", img=Path(__file__)),
        img=Path(__file__),
        stm=FakeStmView(),
        character={"name": "Vika", "hobby": "Kaffee"},
    )
    for key, value in overrides.items():
        if key == "stm" and not hasattr(value, "get"):
            value = FakeStmView(list(value))
        setattr(base, key, value)
    return base


def _patch_storage(monkeypatch, npc_data: SimpleNamespace, template: str) -> None:
    class FakeText:
        def __init__(self, value):
            self._value = value

        def get(self):
            return self._value

    class FakePrompts:
        chat_general_rules = FakeText(template)

    class FakeNpcPaths:
        stm = npc_data.stm
        character_original = FakeText(npc_data.character)
        system_prompt_original = FakeText(npc_data.system_prompt)
        description = FakeText(npc_data.description)
        state = npc_data.state

    class FakeStorage:
        prompts = FakePrompts()
        npc = FakeNpcPaths()
        scene = SimpleNamespace(description=npc_data.scene.description)

    monkeypatch.setattr(npc_turn_service_module, "storage", FakeStorage())


def test_build_chat_messages_uses_prompt_template_with_placeholders(monkeypatch):
    template = """# Role\n{{ROLE}}\n\n# Data\n{{CHARACTER_DATA}}\n\n# Description\n{{CHARACTER_DESCRIPTION}}\n\n# State\n{{CURRENT_STATE}}\n\n# Retrieved\n{{CURRENT_ETM}}\n\n# Rules\nRegel A\n"""

    npc = _build_npc()
    _patch_storage(monkeypatch, npc, template)

    service = NpcTurnService()
    turn_messages = service.build_chat_messages("Hallo")
    system_message = turn_messages[0]

    assert system_message["role"] == "system"
    assert "Bleib in Character" in system_message["content"]
    assert "Regel A" in system_message["content"]
    assert "name: Vika" in system_message["content"]
    assert "hobby: Kaffee" in system_message["content"]
    assert "Beschreibung" in system_message["content"]
    assert "mood: neutral" in system_message["content"]
    assert "(keine zusätzlichen relevanten Erinnerungen)" in system_message["content"]
    assert "{{" not in system_message["content"]


def test_build_chat_messages_uses_leer_for_empty_values(monkeypatch):
    npc = _build_npc(system_prompt="   ", description="", state=" ", relationship=" ", character={})
    _patch_storage(monkeypatch, npc, "{{ROLE}} | {{CHARACTER_DATA}} | {{CHARACTER_DESCRIPTION}} | {{CURRENT_STATE}} | {{CURRENT_ETM}}")

    service = NpcTurnService()
    turn_messages = service.build_chat_messages("Hallo")
    system_message = turn_messages[0]

    assert system_message["content"] == "(leer) | {} | (leer) | (leer) | (keine zusätzlichen relevanten Erinnerungen)"


def test_build_turn_messages_places_system_prompt_before_stm_and_user_message_is_separate(monkeypatch):
    npc = _build_npc(
        stm=[
            Message(
                id="m1",
                timestamp_utc="2026-03-28T10:00:00+00:00",
                role="user",
                content="Hallo",
            ),
            Message(
                id="m2",
                timestamp_utc="2026-03-28T10:00:01+00:00",
                role="assistant",
                content="Hi!",
            ),
        ]
    )
    _patch_storage(monkeypatch, npc, "{{ROLE}} | {{CURRENT_SCENE}} | {{CURRENT_STATE}} | {{CURRENT_ETM}}")

    service = NpcTurnService()
    turn_messages = service.build_chat_messages("Neue Nachricht")
    user_message = turn_messages[-1]

    assert user_message is not None
    assert user_message["role"] == "user"
    assert user_message["content"] == "Neue Nachricht"
    assert [message["role"] for message in turn_messages[:-1]] == [
        "system",
        "user",
        "assistant",
    ]
    assert "Im Buero" in str(turn_messages[0]["content"])
    assert "mood: neutral" in str(turn_messages[0]["content"])


def test_build_turn_messages_includes_retrieved_memories_from_etm_store(monkeypatch, tmp_path):
    npc = _build_npc(
        stm=[
            Message(
                id="m1",
                timestamp_utc="2026-03-28T10:00:00+00:00",
                role="user",
                content="Wir waren gestern in der Bar.",
            ),
            Message(
                id="m2",
                timestamp_utc="2026-03-28T10:00:01+00:00",
                role="assistant",
                content="Da war es ziemlich ruhig.",
            ),
        ]
    )

    class FakeEtmService:
        def load_relevant(self, query_text):
            assert "user: Wir waren gestern in der Bar." in query_text
            assert "assistant: Da war es ziemlich ruhig." in query_text
            assert query_text.endswith("user: Wollen wir wieder in eine Bar gehen?")
            return "- Er erinnert sich an eine ruhige Bar mit guten Gläsern."

    monkeypatch.setattr(npc_turn_service_module, "EtmService", FakeEtmService)
    monkeypatch.setattr(npc_turn_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    _patch_storage(monkeypatch, npc, "{{CURRENT_STATE}}\n---\n{{CURRENT_ETM}}")

    service = NpcTurnService()
    turn_messages = service.build_chat_messages("Wollen wir wieder in eine Bar gehen?")
    system_message = turn_messages[0]

    assert "mood: neutral" in system_message["content"]
    assert "Er erinnert sich an eine ruhige Bar mit guten Gläsern." in system_message["content"]
    assert system_message["content"].count("mood: neutral") == 1


def test_build_turn_messages_skips_retrieval_without_store(monkeypatch, tmp_path):
    npc = _build_npc()
    monkeypatch.setattr(npc_turn_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    _patch_storage(monkeypatch, npc, "{{CURRENT_ETM}}")

    service = NpcTurnService()
    turn_messages = service.build_chat_messages("Hi")

    assert turn_messages[0]["content"] == "(keine zusätzlichen relevanten Erinnerungen)"


def test_build_chat_messages_uses_configured_stm_window_for_retrieval(monkeypatch):
    stm_messages = [
        Message(
            id=f"m{index}",
            timestamp_utc=f"2026-03-28T10:00:0{index}+00:00",
            role="user" if index % 2 == 0 else "assistant",
            content=f"Nachricht {index}",
        )
        for index in range(6)
    ]
    npc = _build_npc(stm=stm_messages)

    captured: dict[str, str] = {}

    class FakeEtmService:
        def load_relevant(self, query_text):
            captured["query"] = query_text
            return ""

    monkeypatch.setattr(npc_turn_service_module, "EtmService", FakeEtmService)
    monkeypatch.setattr(npc_turn_service_module.config, "STM_LATEST_MESSAGES", 3)
    _patch_storage(monkeypatch, npc, "{{CURRENT_ETM}}")

    service = NpcTurnService()
    service.build_chat_messages("Neue Eingabe")

    query_text = captured["query"]
    assert "Nachricht 2" not in query_text
    assert "Nachricht 0" not in query_text
    assert "Nachricht 3" in query_text
    assert "Nachricht 5" in query_text
    assert query_text.endswith("user: Neue Eingabe")


def test_build_chat_messages_appends_user_message(monkeypatch):
    npc = _build_npc()
    _patch_storage(monkeypatch, npc, "{{ROLE}}")

    service = NpcTurnService()
    turn_messages = service.build_chat_messages("Neue Nachricht")

    assert turn_messages[-1] == {"role": "user", "content": "Neue Nachricht"}


def test_finalize_turn_persists_trimmed_messages(monkeypatch):
    make_calls: list[tuple[str, str]] = []
    appended_messages: list[Message] = []

    def fake_make_message(self, role: Literal["user", "assistant", "system"], content: str):
        make_calls.append((role, content))
        return Message(
            id=f"{role}-id",
            timestamp_utc="2026-03-22T10:00:00+00:00",
            role=cast(Literal["user", "assistant", "system"], role),
            content=content,
        )

    class FakeStm:
        def append(self, msg: Message):
            appended_messages.append(msg)

    class FakeNpcPaths:
        stm = FakeStm()

    class FakeStorage:
        npc = FakeNpcPaths()

    monkeypatch.setattr(npc_turn_service_module.NpcTurnService, "_make_message", fake_make_message)
    monkeypatch.setattr(npc_turn_service_module, "storage", FakeStorage())

    service = NpcTurnService()
    service.finalize_turn("  Hallo  ", "  Hi zurück  ")

    assert make_calls == [("user", "Hallo"), ("assistant", "Hi zurück")]
    assert len(appended_messages) == 2
    assert appended_messages[0].id == "user-id"
    assert appended_messages[0].role == "user"
    assert appended_messages[0].content == "Hallo"
    assert appended_messages[1].id == "assistant-id"
    assert appended_messages[1].role == "assistant"
    assert appended_messages[1].content == "Hi zurück"

