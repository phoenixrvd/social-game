from __future__ import annotations

from typing import Callable
from rapidfuzz import fuzz

from engine.config import config
from engine.llm.client import client
from engine.storage import storage
from engine.storage.models import Episode

EMPTY_ETM_TEXT = "(keine zusätzlichen relevanten Erinnerungen)"


class EtmService:
    def __init__(self) -> None:
        self._local_embedding_fn: Callable[[list[str]], list[list[float]]] | None = None

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
        matches = self._query_etm_texts(query_text)
        memories = self._deduplicate_memories(matches)
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

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        cleaned = [text for text in texts if text.strip()]
        if not cleaned:
            return []
        embedding_fn = self._local_embedding_function()
        embeddings = embedding_fn(cleaned)
        return [list(vector) for vector in embeddings]

    def _store_etm_text(self, text: str) -> None:
        cleaned_text = text.strip()
        if not cleaned_text:
            return
        storage.npc.etm.append(
            text=cleaned_text,
            embedding=self._embed_texts([cleaned_text])[0],
        )

    def _query_etm_texts(self, query_text: str) -> list[str]:
        top_k = config.ETM_RETRIEVAL_TOP_K
        cleaned_query = query_text.strip()
        if top_k <= 0 or not cleaned_query:
            return []

        episodes = storage.npc.etm.get()
        if not episodes:
            return []
        query_embedding = self._embed_texts([cleaned_query])[0]
        query_episode = Episode(
            id="query",
            text=cleaned_query,
            embedding=query_embedding,
            created_at="",
        )

        matches = self._collect_matches(episodes, query_episode)
        matches.sort(key=lambda item: item[0])
        return [text for _, text in matches[:top_k]]

    def _collect_matches(
        self,
        episodes: list[Episode],
        query_episode: Episode,
    ) -> list[tuple[float, str]]:
        matches: list[tuple[float, str]] = []
        for episode in episodes:
            if not episode.is_similar(query_episode):
                continue
            matches.append((episode.distance_to(query_episode), episode.text))
        return matches

    def _local_embedding_function(self) -> Callable[[list[str]], list[list[float]]]:
        if self._local_embedding_fn is not None:
            return self._local_embedding_fn

        from fastembed import TextEmbedding

        cache_dir = storage.etm_fastembed_cache
        cache_dir.mkdir(parents=True, exist_ok=True)

        model = TextEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_dir=str(cache_dir),
        )

        def fn(texts: list[str]) -> list[list[float]]:
            return [[float(value) for value in vector] for vector in model.embed(texts)]

        self._local_embedding_fn = fn
        return fn


    def _deduplicate_memories(self, matches: list[str]) -> list[str]:
        kept_similarity_threshold = 92
        kept: list[str] = []

        for match in matches:
            candidate = match.strip()
            if not candidate:
                continue
            if any(fuzz.ratio(candidate, item) > kept_similarity_threshold for item in kept):
                continue
            kept.append(candidate)

        return kept[: config.ETM_RETRIEVAL_TOP_K]

