from pathlib import Path

import engine.services.npc_turn_service as npc_turn_service_module
from engine.models import Npc, Scene, ShortMemoryMessage
from engine.services.npc_turn_service import NpcTurnService


def _build_npc(**overrides) -> Npc:
    base = Npc(
        npc_id="vika",
        description="Beschreibung",
        system_prompt="Bleib in Character",
        state="mood: neutral",
        ltm="Kennt den Spieler",
        scene=Scene(scene_id="office", description="Im Buero"),
        img=Path(__file__),
        character={"name": "Vika", "hobby": "Kaffee"},
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_build_turn_messages_uses_prompt_template_with_placeholders(monkeypatch):
    template = """# Role\n{{ROLE}}\n\n# Data\n{{CHARACTER_DATA}}\n\n# Description\n{{CHARACTER_DESCRIPTION}}\n\n# LTM\n{{CHARACTER_LONG_TERM_MEMORY}}\n\n# Rules\nRegel A\n"""

    npc = _build_npc()

    class FakeNpcStore:
        def load(self):
            return npc

    monkeypatch.setattr(npc_turn_service_module, "NpcStore", FakeNpcStore)

    def fake_load_text(path):
        if path == npc_turn_service_module.config.PROJECT_ROOT / "prompts" / "chat_general_rules.md":
            return template
        raise AssertionError(f"Unerwarteter Pfad: {path}")

    monkeypatch.setattr(npc_turn_service_module, "load_text", fake_load_text)

    service = NpcTurnService()
    turn_messages = service.build_turn_messages()
    system_message = turn_messages[0]

    assert system_message["role"] == "system"
    assert "Bleib in Character" in system_message["content"]
    assert "Regel A" in system_message["content"]
    assert "name: Vika" in system_message["content"]
    assert "hobby: Kaffee" in system_message["content"]
    assert "Beschreibung" in system_message["content"]
    assert "Kennt den Spieler" in system_message["content"]
    assert "{{" not in system_message["content"]


def test_build_turn_messages_uses_leer_for_empty_values(monkeypatch):
    npc = _build_npc(system_prompt="   ", description="", ltm=" ", character={})

    class FakeNpcStore:
        def load(self):
            return npc

    monkeypatch.setattr(npc_turn_service_module, "NpcStore", FakeNpcStore)

    def fake_load_text(path):
        if path == npc_turn_service_module.config.PROJECT_ROOT / "prompts" / "chat_general_rules.md":
            return "{{ROLE}} | {{CHARACTER_DATA}} | {{CHARACTER_DESCRIPTION}} | {{CHARACTER_LONG_TERM_MEMORY}}"
        raise AssertionError(f"Unerwarteter Pfad: {path}")

    monkeypatch.setattr(npc_turn_service_module, "load_text", fake_load_text)

    service = NpcTurnService()
    turn_messages = service.build_turn_messages()
    system_message = turn_messages[0]

    assert system_message["content"] == "(leer) | {} | (leer) | (leer)"


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

    def fake_load_text(path):
        if path == npc_turn_service_module.config.PROJECT_ROOT / "prompts" / "chat_general_rules.md":
            return "{{ROLE}} | {{CURRENT_SCENE}} | {{NPC_STATE}}"
        raise AssertionError(f"Unerwarteter Pfad: {path}")

    monkeypatch.setattr(npc_turn_service_module, "load_text", fake_load_text)

    service = NpcTurnService()
    turn_messages = service.build_turn_messages()
    user_message = service.build_user_message("Neue Nachricht")

    assert user_message["role"] == "user"
    assert user_message["content"] == "Neue Nachricht"
    assert [message["role"] for message in turn_messages] == [
        "system",     # system prompt (inkl. scene + state)
        "user",       # stm[0]
        "assistant",  # stm[1]
    ]
    assert "Im Buero" in str(turn_messages[0]["content"])
    assert "mood: neutral" in str(turn_messages[0]["content"])
