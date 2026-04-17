from __future__ import annotations

from typing import cast

import yaml
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
)

from engine.config import config
from engine.models import Npc
from engine.storage import storage
from engine.services.etm_retrieval_service import EMPTY_ETM_TEXT, EtmRetrievalService
from engine.stores.npc_store import NpcStore

EMPTY_PLACEHOLDER = "(leer)"


class NpcTurnService:
    def __init__(self) -> None:
        self.npc_store = NpcStore()
        self.etm_retrieval = EtmRetrievalService()
        self.user_message: ChatCompletionMessageParam | None = None

    def _build_turn_messages_for_context(
        self,
        npc: Npc,
        retrieved_memories: str,
    ) -> list[ChatCompletionMessageParam]:
        system_prompt = self._build_system_prompt(npc, retrieved_memories)
        system_message: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": system_prompt,
        }

        memory_messages = [
            self._to_message_param(message.role, message.content)
            for message in npc.stm
        ]
        return [system_message, *memory_messages]

    @staticmethod
    def _to_message_param(role: str, content: str) -> ChatCompletionMessageParam:
        """Convert role and content to typed message param."""
        return cast(ChatCompletionMessageParam, cast(object, {"role": role, "content": content}))

    @staticmethod
    def _build_system_prompt(npc: Npc, retrieved_memories: str) -> str:
        character_yaml = yaml.dump(npc.character, allow_unicode=True, sort_keys=False).strip()
        base_prompt = storage.prompts.chat_general_rules.get().strip()

        replacements = {
            "{{ROLE}}": npc.system_prompt.strip() or EMPTY_PLACEHOLDER,
            "{{CHARACTER_DATA}}": character_yaml or EMPTY_PLACEHOLDER,
            "{{CHARACTER_DESCRIPTION}}": npc.description.strip() or EMPTY_PLACEHOLDER,
            "{{CURRENT_SCENE}}": npc.scene.description.strip() or EMPTY_PLACEHOLDER,
            "{{CURRENT_STATE}}": npc.state.strip() or EMPTY_PLACEHOLDER,
            "{{CURRENT_ETM}}": retrieved_memories,
        }

        prompt = base_prompt
        for placeholder, value in replacements.items():
            prompt = prompt.replace(placeholder, value)
        return prompt

    def build_chat_messages(
        self,
        player_input: str,
    ) -> list[ChatCompletionMessageParam]:
        npc = self.npc_store.load()
        retrieval_query = self._build_retrieval_query(npc, player_input)
        retrieved_memories = self.etm_retrieval.load_relevant(npc, retrieval_query) or EMPTY_ETM_TEXT
        user_message = self._to_message_param("user", player_input.strip())
        self.user_message = user_message
        turn_messages = self._build_turn_messages_for_context(npc, retrieved_memories)
        return [*turn_messages, user_message]

    @staticmethod
    def _build_retrieval_query(npc: Npc, player_input: str) -> str:
        context_block = npc.stm.as_string_short(last_n=config.ETM_RETRIEVAL_QUERY_LAST_N_STM_MESSAGES) if npc.stm else ""
        player_line = f"user: {player_input.strip()}"
        if not context_block:
            return player_line
        return "\n".join([context_block, player_line])
