from __future__ import annotations

from uuid import uuid4

from engine.llm.client import embed_texts, run_prompt_small
from engine.models import Npc, ShortMemoryMessage
from engine.storage import storage
from engine.services.memory_format import format_short_memory
from engine.stores.etm_vector_store import EtmVectorStore
from engine.stores.npc_store import NpcStore


class EtmUpdateService:
    def __init__(self) -> None:
        self.npc_store = NpcStore()

    def run(self, npc: Npc, batch: list[ShortMemoryMessage]) -> str:
        episode = self._create_episode(batch)
        embedding = embed_texts([episode])[0]
        store = EtmVectorStore(storage.npc.etm_chroma)
        store.add(episode, embedding, str(uuid4()))

        batch_ids = [message.id for message in batch]
        self.npc_store.remove_stm_by_ids(batch_ids)
        return episode

    @staticmethod
    def _create_episode(batch: list[ShortMemoryMessage]) -> str:
        stm_text = format_short_memory(batch)
        prompt = (
            storage.prompts.etm_update.get()
            .strip()
            .replace("{{SHORT_TERM_MEMORY}}", stm_text)
        )
        return run_prompt_small(prompt).strip()

