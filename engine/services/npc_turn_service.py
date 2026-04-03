from __future__ import annotations

from typing import cast

import yaml
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from engine.config import config
from engine.fs_utils import load_text
from engine.models import ShortMemoryMessage
from engine.stores.npc_store import NpcStore


class NpcTurnService:
    def __init__(self) -> None:
        self.npc_store = NpcStore()

    def build_turn_messages(self) -> list[ChatCompletionMessageParam]:
        npc = self.npc_store.load()

        character = yaml.dump(npc.character, allow_unicode=True, sort_keys=False).strip()
        system_prompt = (
            load_text(config.PROJECT_ROOT / "prompts" / "chat_general_rules.md").strip()
            .replace("{{ROLE}}", npc.system_prompt.strip() or "(leer)")
            .replace("{{CHARACTER_DATA}}", character or "(leer)")
            .replace("{{CHARACTER_DESCRIPTION}}", npc.description.strip() or "(leer)")
            .replace("{{CHARACTER_LONG_TERM_MEMORY}}", npc.ltm.strip() or "(leer)")
            .replace("{{CURRENT_SCENE}}", npc.scene.description.strip() or "(leer)")
            .replace("{{NPC_STATE}}", str(npc.state).strip() if npc.state is not None else "(leer)")
        )

        memory_messages = [self._memory_message(message) for message in npc.stm]
        system_message: ChatCompletionSystemMessageParam = {"role": "system", "content": system_prompt}
        return cast(list[ChatCompletionMessageParam], [system_message, *memory_messages])

    def build_user_message(self, player_input: str) -> ChatCompletionUserMessageParam:
        return {
            "role": "user",
            "content": player_input.strip(),
        }

    def _memory_message(self, message: ShortMemoryMessage) -> ChatCompletionMessageParam:
        return cast(
            ChatCompletionMessageParam,
            cast(object, {"role": message.role, "content": message.content}),
        )


