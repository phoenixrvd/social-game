from __future__ import annotations

from engine.client import client
from engine.storage import storage


class UserProfileService:
    @staticmethod
    def _format_stm_for_profile(stm_text: str) -> str:
        if not stm_text.strip():
            return "(keine Nachrichten)"
        return stm_text

    def run_update(self) -> str:
        """Update user profile based on recent dialog."""
        prompt = self._build_prompt()
        profile = client.run_prompt_small(prompt).strip()
        storage.npc.user_profile_runtime.save(profile)
        return profile

    def _build_prompt(self) -> str:
        """Build prompt for user profile update."""
        current_user_profile = storage.npc.user_profile or "(kein Profil)"
        short_term_memory = self._format_stm_for_profile(storage.npc.stm.text_latest)
        current_scene = storage.scene.description.strip() or "(keine Szene)"
        current_state = storage.npc.state.strip() or "(kein State)"

        replacements = {
            "{{CURRENT_USER_PROFILE}}": current_user_profile,
            "{{SHORT_TERM_MEMORY}}": short_term_memory,
            "{{CURRENT_SCENE}}": current_scene,
            "{{CURRENT_STATE}}": current_state,
        }

        prompt = storage.prompts.user_profile_update.get().strip()
        for placeholder, value in replacements.items():
            prompt = prompt.replace(placeholder, value)
        return prompt
