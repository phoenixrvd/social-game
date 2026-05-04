from __future__ import annotations

import math

from engine.config import config
from engine.client import client
from engine.storage import storage
from engine.storage.models import Episode

EMPTY_ETM_TEXT = "(keine zusätzlichen relevanten Erinnerungen)"


class EtmService:
    def compress_stm(self) -> str:
        batch_messages = storage.npc.stm.batch_messages()
        if not batch_messages:
            return ""

        batch_text = storage.npc.stm.batch_text_short
        episode = self._create_episode(batch_text)
        self._store_etm_text(episode)
        storage.npc.stm.remove(batch_messages)
        return episode

    def load_relevant(self, query_text: str) -> str:
        memories = self._query_etm_texts(query_text)
        if not memories:
            return EMPTY_ETM_TEXT
        return "\n".join(f"- {memory}" for memory in memories)

    @staticmethod
    def _create_episode(stm_text: str) -> str:
        prompt = (
            storage.prompts.etm_update.get()
            .strip()
            .replace("{{SHORT_TERM_MEMORY}}", stm_text)
        )
        return client.run_prompt_small(prompt).strip()

    def _embed_texts(self, text: str) -> list[float]:
        cleaned = text.strip()
        if not cleaned:
            return []
        return client.embed_texts(cleaned)

    def _store_etm_text(self, text: str) -> None:
        cleaned_text = text.strip()
        if not cleaned_text:
            return
        storage.npc.etm.append(
            text=cleaned_text,
            embedding=self._embed_texts(cleaned_text),
        )

    def _query_etm_texts(self, query_text: str) -> list[str]:
        top_k = config.ETM_RETRIEVAL_TOP_K
        cleaned_query = query_text.strip()
        if top_k <= 0 or not cleaned_query:
            return []

        episodes = storage.npc.etm.get()
        if not episodes:
            return []

        query_embedding = self._embed_texts(cleaned_query)
        matches = self._collect_matches(episodes, query_embedding)
        matches.sort(key=lambda item: item[0])
        deduplicated = self._deduplicate_memories(matches)
        return [episode.text for episode in deduplicated[:top_k]]

    def _collect_matches(
        self,
        episodes: list[Episode],
        query_embedding: list[float],
    ) -> list[tuple[float, Episode]]:
        matches: list[tuple[float, Episode]] = []
        for episode in episodes:
            distance = self._embedding_distance(episode.embedding, query_embedding)
            if distance > config.ETM_RETRIEVAL_MAX_DISTANCE:
                continue
            matches.append((distance, episode))
        return matches

    def _deduplicate_memories(self, matches: list[tuple[float, Episode]]) -> list[Episode]:
        kept: list[Episode] = []

        for _, episode in matches:
            if not episode.text.strip():
                continue
            if any(
                self._embedding_distance(episode.embedding, kept_episode.embedding)
                <= config.ETM_DEDUPLICATION_MAX_DISTANCE
                for kept_episode in kept
            ):
                continue
            kept.append(episode)

        return kept

    def _embedding_distance(self, left: list[float], right: list[float]) -> float:
        return 1.0 - self._cosine_similarity(left, right)

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        dot_product = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return dot_product / (left_norm * right_norm)
