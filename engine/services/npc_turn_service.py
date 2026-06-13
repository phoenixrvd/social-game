from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, cast
from uuid import uuid4

import yaml
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
)

from engine.services.etm_service import EMPTY_ETM_TEXT, EtmService
from engine.storage import storage
from engine.storage.models import Message

EMPTY_PLACEHOLDER = "(leer)"


class NpcTurnService:
    def __init__(self) -> None:
        self.etm_retrieval = EtmService()

    def _build_turn_messages_for_context(
        self,
        retrieved_memories: str,
    ) -> list[ChatCompletionMessageParam]:
        system_prompt = self._build_system_prompt(retrieved_memories)
        system_message: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": system_prompt,
        }

        memory_messages = [
            self._to_message_param(message.role, message.content)
            for message in storage.npc.stm.get()
        ]
        return [system_message, *memory_messages]

    @staticmethod
    def _to_message_param(role: str, content: str) -> ChatCompletionMessageParam:
        """Überführt Rolle und Inhalt in einen typisierten Chat-Parameter."""
        return cast(ChatCompletionMessageParam, cast(object, {"role": role, "content": content}))

    @staticmethod
    def _build_system_prompt(retrieved_memories: str) -> str:
        character = storage.npc.character_original.get()
        character_yaml = yaml.dump(character, allow_unicode=True, sort_keys=False).strip()
        base_prompt = storage.prompts.chat_general_rules.get().strip()

        role_text = storage.npc.system_prompt_original.get().strip() or EMPTY_PLACEHOLDER
        character_description = storage.npc.description.get().strip() or EMPTY_PLACEHOLDER
        scene_description = storage.scene.description.strip() or EMPTY_PLACEHOLDER
        state_text = storage.npc.state.strip() or EMPTY_PLACEHOLDER
        user_profile = storage.avatar.description.get().strip() or EMPTY_PLACEHOLDER

        replacements = {
            "{{ROLE}}": role_text,
            "{{CHARACTER_DATA}}": character_yaml or EMPTY_PLACEHOLDER,
            "{{CHARACTER_DESCRIPTION}}": character_description,
            "{{CURRENT_SCENE}}": scene_description,
            "{{CURRENT_STATE}}": state_text,
            "{{CURRENT_ETM}}": retrieved_memories,
            "{{USER_PROFILE}}": user_profile,
        }

        prompt = base_prompt
        for placeholder, value in replacements.items():
            prompt = prompt.replace(placeholder, value)
        return prompt

    def build_chat_messages(
        self,
        player_input: str,
    ) -> list[ChatCompletionMessageParam]:
        retrieval_query = self._build_retrieval_query(player_input)
        retrieved_memories = self.etm_retrieval.load_relevant(retrieval_query) or EMPTY_ETM_TEXT
        user_message = self._to_message_param("user", player_input.strip())
        turn_messages = self._build_turn_messages_for_context(retrieved_memories)
        return [*turn_messages, user_message]

    def finalize_turn(self, player_input: str, assistant_reply: str) -> None:
        user_content = player_input.strip()
        assistant_content = assistant_reply.strip()
        user_message = self._make_message("user", user_content)
        assistant_message = self._make_message("assistant", assistant_content)
        storage.npc.stm.append(user_message)
        storage.npc.stm.append(assistant_message)

    @staticmethod
    def _make_message(
        role: Literal["user", "assistant", "system"],
        content: str,
    ) -> Message:
        return Message(
            id=str(uuid4()),
            timestamp_utc=datetime.now(UTC).isoformat(),
            role=role,
            content=content,
        )

    @staticmethod
    def _build_retrieval_query(player_input: str) -> str:
        player_line = f"user: {player_input.strip()}"
        messages = storage.npc.stm.get()
        if not messages:
            return player_line

        return "\n".join([storage.npc.stm.text_short_latest, player_line])
