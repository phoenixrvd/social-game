from __future__ import annotations

from rapidfuzz import fuzz

from engine.config import config
from engine.llm.client import embed_texts
from engine.models import Npc
from engine.storage import storage
from engine.stores.etm_vector_store import EtmVectorStore

EMPTY_ETM_TEXT = "(keine zusätzlichen relevanten Erinnerungen)"


class EtmRetrievalService:
    def load_relevant(self, npc: Npc, query_text: str) -> str:
        cleaned_query = query_text.strip()
        if not cleaned_query:
            return EMPTY_ETM_TEXT

        store_path = storage.npc.etm_chroma
        if not store_path.exists():
            return EMPTY_ETM_TEXT

        query_embedding = embed_texts([cleaned_query])[0]
        matches = EtmVectorStore(store_path).query(
            query_embedding,
            config.ETM_RETRIEVAL_TOP_K,
            config.ETM_RETRIEVAL_MAX_DISTANCE,
        )
        filtered = self._deduplicate_memories(matches)
        return self._render_memories(filtered)

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

    @staticmethod
    def _render_memories(memories: list[str]) -> str:
        if not memories:
            return EMPTY_ETM_TEXT
        return "\n".join(f"- {memory}" for memory in memories)
