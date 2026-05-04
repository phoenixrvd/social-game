from __future__ import annotations

from types import SimpleNamespace

import engine.services.user_profile_service as user_profile_service_module
from engine.services.user_profile_service import UserProfileService


class FakeText:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


def test_format_stm_for_profile_keeps_assistant_label() -> None:
    stm_text = "user: Hallo\nassistant: Hi\nassistant: Wie geht's?"

    formatted = UserProfileService._format_stm_for_profile(stm_text)

    assert formatted == "user: Hallo\nassistant: Hi\nassistant: Wie geht's?"


def test_build_prompt_includes_formatted_stm_and_npc_context(monkeypatch) -> None:
    fake_storage = SimpleNamespace(
        prompts=SimpleNamespace(
            user_profile_update=FakeText(
                "{{CURRENT_USER_PROFILE}}\n{{SHORT_TERM_MEMORY}}\n{{CURRENT_SCENE}}\n{{CURRENT_STATE}}"
            )
        ),
        npc=SimpleNamespace(
            user_profile="- kennt Kaffee",
            stm=SimpleNamespace(text_latest="user: A\nassistant: B"),
            state="ruhig",
        ),
        scene=SimpleNamespace(description="Cafe"),
    )
    monkeypatch.setattr(user_profile_service_module, "storage", fake_storage)

    prompt = UserProfileService()._build_prompt()

    assert "- kennt Kaffee" in prompt
    assert "user: A\nassistant: B" in prompt
    assert "Cafe" in prompt
    assert "ruhig" in prompt



