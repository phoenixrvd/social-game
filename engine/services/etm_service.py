from __future__ import annotations

from uuid import uuid4

from rapidfuzz import fuzz

from engine.config import config
from engine.llm.client import client
from engine.models import Stm
from engine.storage import storage
from engine.stores.etm_vector_store import EtmVectorStore
from engine.stores.npc_store import NpcStore

EMPTY_ETM_TEXT = "(keine zusätzlichen relevanten Erinnerungen)"


class EtmService:
    def __init__(self) -> None:
        self.npc_store = NpcStore()

    def compress_stm(self) -> str:
        batch = self.npc_store.load().stm.get_batch()
        if not batch:
            return ""

        episode = self._create_episode(batch)
        embedding = client.embed_texts([episode])[0]
        EtmVectorStore(storage.npc.etm_chroma).add(episode, embedding, str(uuid4()))

        self.npc_store.remove_stm_by_ids([message.id for message in batch])
        return episode

    def load_relevant(self, query_text: str) -> str:
        cleaned_query = query_text.strip()
        if not cleaned_query:
            return EMPTY_ETM_TEXT

        store_path = storage.npc.etm_chroma
        if not store_path.exists():
            return EMPTY_ETM_TEXT

        query_embedding = client.embed_texts([cleaned_query])[0]
        matches = EtmVectorStore(store_path).query(
            query_embedding,
            config.ETM_RETRIEVAL_TOP_K,
            config.ETM_RETRIEVAL_MAX_DISTANCE,
        )
        memories = self._deduplicate_memories(matches)
        if not memories:
            return EMPTY_ETM_TEXT
        return "\n".join(f"- {memory}" for memory in memories)

    @staticmethod
    def _create_episode(batch: Stm) -> str:
        stm_text = batch.as_string_short()
        prompt = (
            storage.prompts.etm_update.get()
            .strip()
            .replace("{{SHORT_TERM_MEMORY}}", stm_text)
        )
        return client.run_prompt_small(prompt).strip()

    def _deduplicate_memories(self, matches: list[str]) -> list[str]:
        kept_similarity_threshold = 92
        kept: list[str] = []

        for match in matches:
            candidate = match.strip()
            if not candidate:
                continue
            if self._is_similar_to_any(candidate, kept, kept_similarity_threshold):
                continue
            kept.append(candidate)

        return kept[: config.ETM_RETRIEVAL_TOP_K]

    @staticmethod
    def _is_similar_to_any(candidate: str, items: list[str], threshold: int) -> bool:
        return any(fuzz.ratio(candidate, item) > threshold for item in items)

