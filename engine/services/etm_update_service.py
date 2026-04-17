from __future__ import annotations

from uuid import uuid4

from engine.llm.client import embed_texts, run_prompt_small
from engine.models import Stm
from engine.storage import storage
from engine.stores.etm_vector_store import EtmVectorStore
from engine.stores.npc_store import NpcStore


class EtmUpdateService:
    def __init__(self) -> None:
        self.npc_store = NpcStore()

    def run(self) -> str:
        batch = self.npc_store.load().stm.get_batch()
        episode = self._create_episode(batch)
        embedding = embed_texts([episode])[0]
        store = EtmVectorStore(storage.npc.etm_chroma)
        store.add(episode, embedding, str(uuid4()))

        batch_ids = [message.id for message in batch]
        self.npc_store.remove_stm_by_ids(batch_ids)
        return episode

    @staticmethod
    def _create_episode(batch: Stm) -> str:
        stm_text = batch.as_string_short()
        prompt = (
            storage.prompts.etm_update.get()
            .strip()
            .replace("{{SHORT_TERM_MEMORY}}", stm_text)
        )
        return run_prompt_small(prompt).strip()

