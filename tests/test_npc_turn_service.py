from pathlib import Path

import engine.services.npc_turn_service as npc_turn_service_module
from engine.models import Npc, Scene, ShortMemoryMessage, Stm
from engine.services.npc_turn_service import NpcTurnService


def _build_npc(**overrides) -> Npc:
    base = Npc(
        npc_id="vika",
        description="Beschreibung",
        system_prompt="Bleib in Character",
        state="mood: neutral",
        relationship="Kennt den Spieler",
        scene=Scene(scene_id="office", description="Im Buero"),
        img_current=Path(__file__),
        character={"name": "Vika", "hobby": "Kaffee"},
    )
    for key, value in overrides.items():
        if key == "stm" and not isinstance(value, Stm):
            value = Stm(value)
        setattr(base, key, value)
    return base


def test_build_chat_messages_uses_prompt_template_with_placeholders(monkeypatch):
    template = """# Role\n{{ROLE}}\n\n# Data\n{{CHARACTER_DATA}}\n\n# Description\n{{CHARACTER_DESCRIPTION}}\n\n# State\n{{CURRENT_STATE}}\n\n# Retrieved\n{{CURRENT_ETM}}\n\n# Rules\nRegel A\n"""

    npc = _build_npc()

    class FakeNpcStore:
        def load(self):
            return npc

    monkeypatch.setattr(npc_turn_service_module, "NpcStore", FakeNpcStore)

    class FakePrompt:
        def get(self):
            return template

    class FakePrompts:
        chat_general_rules = FakePrompt()

    class FakeStorage:
        prompts = FakePrompts()

    monkeypatch.setattr(npc_turn_service_module, "storage", FakeStorage())

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

    class FakeNpcStore:
        def load(self):
            return npc

    monkeypatch.setattr(npc_turn_service_module, "NpcStore", FakeNpcStore)

    class FakePrompt:
        def get(self):
            return "{{ROLE}} | {{CHARACTER_DATA}} | {{CHARACTER_DESCRIPTION}} | {{CURRENT_STATE}} | {{CURRENT_ETM}}"

    class FakePrompts:
        chat_general_rules = FakePrompt()

    class FakeStorage:
        prompts = FakePrompts()

    monkeypatch.setattr(npc_turn_service_module, "storage", FakeStorage())

    service = NpcTurnService()
    turn_messages = service.build_chat_messages("Hallo")
    system_message = turn_messages[0]

    assert system_message["content"] == "(leer) | {} | (leer) | (leer) | (keine zusätzlichen relevanten Erinnerungen)"


def test_build_turn_messages_places_system_prompt_before_stm_and_user_message_is_separate(monkeypatch):
    npc = _build_npc(
        stm=[
            ShortMemoryMessage(
                id="m1",
                timestamp_utc="2026-03-28T10:00:00+00:00",
                role="user",
                content="Hallo",
            ),
            ShortMemoryMessage(
                id="m2",
                timestamp_utc="2026-03-28T10:00:01+00:00",
                role="assistant",
                content="Hi!",
            ),
        ]
    )

    class FakeNpcStore:
        def load(self):
            return npc

    monkeypatch.setattr(npc_turn_service_module, "NpcStore", FakeNpcStore)

    class FakePrompt:
        def get(self):
            return "{{ROLE}} | {{CURRENT_SCENE}} | {{CURRENT_STATE}} | {{CURRENT_ETM}}"

    class FakePrompts:
        chat_general_rules = FakePrompt()

    class FakeStorage:
        prompts = FakePrompts()

    monkeypatch.setattr(npc_turn_service_module, "storage", FakeStorage())

    service = NpcTurnService()
    turn_messages = service.build_chat_messages("Neue Nachricht")
    user_message = turn_messages[-1]

    assert user_message is not None
    assert user_message["role"] == "user"
    assert user_message["content"] == "Neue Nachricht"
    assert [message["role"] for message in turn_messages[:-1]] == [
        "system",     # system prompt (inkl. scene + state)
        "user",       # stm[0]
        "assistant",  # stm[1]
    ]
    assert "Im Buero" in str(turn_messages[0]["content"])
    assert "mood: neutral" in str(turn_messages[0]["content"])


def test_build_turn_messages_includes_retrieved_memories_from_chroma(monkeypatch, tmp_path):
    npc = _build_npc(
        stm=[
            ShortMemoryMessage(
                id="m1",
                timestamp_utc="2026-03-28T10:00:00+00:00",
                role="user",
                content="Wir waren gestern in der Bar.",
            ),
            ShortMemoryMessage(
                id="m2",
                timestamp_utc="2026-03-28T10:00:01+00:00",
                role="assistant",
                content="Da war es ziemlich ruhig.",
            ),
        ]
    )

    class FakeNpcStore:
        def load(self):
            return npc

    class FakeEtmService:
        def load_relevant(self, query_text):
            assert "user: Wir waren gestern in der Bar." in query_text
            assert "assistant: Da war es ziemlich ruhig." in query_text
            assert query_text.endswith("user: Wollen wir wieder in eine Bar gehen?")
            return "- Er erinnert sich an eine ruhige Bar mit guten Gläsern."

    monkeypatch.setattr(npc_turn_service_module, "NpcStore", FakeNpcStore)
    monkeypatch.setattr(npc_turn_service_module, "EtmService", FakeEtmService)
    monkeypatch.setattr(npc_turn_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    class FakePrompt:
        def get(self):
            return "{{CURRENT_STATE}}\n---\n{{CURRENT_ETM}}"

    class FakePrompts:
        chat_general_rules = FakePrompt()

    class FakeStorage:
        prompts = FakePrompts()

    monkeypatch.setattr(npc_turn_service_module, "storage", FakeStorage())

    service = NpcTurnService()
    turn_messages = service.build_chat_messages("Wollen wir wieder in eine Bar gehen?")
    system_message = turn_messages[0]

    assert "mood: neutral" in system_message["content"]
    assert "Er erinnert sich an eine ruhige Bar mit guten Gläsern." in system_message["content"]
    assert system_message["content"].count("mood: neutral") == 1


def test_build_turn_messages_skips_retrieval_without_store(monkeypatch, tmp_path):
    npc = _build_npc()

    class FakeNpcStore:
        def load(self):
            return npc

    monkeypatch.setattr(npc_turn_service_module, "NpcStore", FakeNpcStore)
    monkeypatch.setattr(npc_turn_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    class FakePrompt:
        def get(self):
            return "{{CURRENT_ETM}}"

    class FakePrompts:
        chat_general_rules = FakePrompt()

    class FakeStorage:
        prompts = FakePrompts()

    monkeypatch.setattr(npc_turn_service_module, "storage", FakeStorage())

    service = NpcTurnService()
    turn_messages = service.build_chat_messages("Hi")

    assert turn_messages[0]["content"] == "(keine zusätzlichen relevanten Erinnerungen)"


def test_build_chat_messages_uses_configured_stm_window_for_retrieval(monkeypatch):
    stm_messages = [
        ShortMemoryMessage(
            id=f"m{index}",
            timestamp_utc=f"2026-03-28T10:00:0{index}+00:00",
            role="user" if index % 2 == 0 else "assistant",
            content=f"Nachricht {index}",
        )
        for index in range(6)
    ]
    npc = _build_npc(stm=stm_messages)

    class FakeNpcStore:
        def load(self):
            return npc

    captured: dict[str, str] = {}

    class FakeEtmService:
        def load_relevant(self, query_text):
            captured["query"] = query_text
            return ""

    monkeypatch.setattr(npc_turn_service_module, "NpcStore", FakeNpcStore)
    monkeypatch.setattr(npc_turn_service_module, "EtmService", FakeEtmService)
    monkeypatch.setattr(npc_turn_service_module.config, "ETM_RETRIEVAL_QUERY_LAST_N_STM_MESSAGES", 3)

    class FakePrompt:
        def get(self):
            return "{{CURRENT_ETM}}"

    class FakePrompts:
        chat_general_rules = FakePrompt()

    class FakeStorage:
        prompts = FakePrompts()

    monkeypatch.setattr(npc_turn_service_module, "storage", FakeStorage())

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

    class FakeNpcStore:
        def load(self):
            return npc

    monkeypatch.setattr(npc_turn_service_module, "NpcStore", FakeNpcStore)

    class FakePrompt:
        def get(self):
            return "{{ROLE}}"

    class FakePrompts:
        chat_general_rules = FakePrompt()

    class FakeStorage:
        prompts = FakePrompts()

    monkeypatch.setattr(npc_turn_service_module, "storage", FakeStorage())

    service = NpcTurnService()
    turn_messages = service.build_chat_messages("Neue Nachricht")

    assert turn_messages[-1] == {"role": "user", "content": "Neue Nachricht"}


def test_finalize_turn_persists_trimmed_messages(monkeypatch):
    calls: list[tuple[str, str]] = []

    class FakeNpcStore:
        def append_stm_turn(self, user_content: str, assistant_content: str):
            calls.append((user_content, assistant_content))

    monkeypatch.setattr(npc_turn_service_module, "NpcStore", FakeNpcStore)

    service = NpcTurnService()
    service.finalize_turn("  Hallo  ", "  Hi zurück  ")

    assert calls == [("Hallo", "Hi zurück")]

