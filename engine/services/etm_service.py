from __future__ import annotations

from contextlib import closing
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from rapidfuzz import fuzz
from uuid import uuid4

from engine.config import config
from engine.llm.client import client
from engine.models import Stm
from engine.storage import storage
from engine.stores.npc_store import NpcStore

EMPTY_ETM_TEXT = "(keine zusätzlichen relevanten Erinnerungen)"


class EtmService:
    def __init__(self) -> None:
        self.npc_store = NpcStore()
        self._local_embedding_fn: Callable[[list[str]], list[list[float]]] | None = None

    def compress_stm(self) -> str:
        batch = self.npc_store.load().stm.get_batch()
        if not batch:
            return ""

        episode = self._create_episode(batch)
        self._store_etm_text(storage.npc.etm_sqlite, episode)
        self.npc_store.remove_stm_by_ids([message.id for message in batch])
        return episode

    def load_relevant(self, query_text: str) -> str:
        matches = self._query_etm_texts(storage.npc.etm_sqlite, query_text)
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

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        cleaned = [text for text in texts if text.strip()]
        if not cleaned:
            return []
        embedding_fn = self._local_embedding_function()
        embeddings = embedding_fn(cleaned)
        return [list(vector) for vector in embeddings]

    def _store_etm_text(self, path: Path, text: str) -> None:
        cleaned_text = text.strip()
        if not cleaned_text:
            return

        with closing(self._connect_etm_store(path)) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO etm_entries (entry_id, text, embedding, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    cleaned_text,
                    json.dumps(self._embed_texts([cleaned_text])[0]),
                    self._utc_timestamp(),
                ),
            )
            connection.commit()

    def _query_etm_texts(self, path: Path, query_text: str) -> list[str]:
        top_k = config.ETM_RETRIEVAL_TOP_K
        max_distance = config.ETM_RETRIEVAL_MAX_DISTANCE
        cleaned_query = query_text.strip()
        if top_k <= 0 or not cleaned_query or not path.exists():
            return []

        query_embedding = self._embed_texts([cleaned_query])[0]
        with closing(self._connect_etm_store(path)) as connection:
            rows = connection.execute("SELECT text, embedding FROM etm_entries").fetchall()
        if not rows:
            return []

        matches = self._collect_matches(rows, query_embedding, max_distance)
        matches.sort(key=lambda item: item[0])
        return [text for _, text in matches[:top_k]]

    def _collect_matches(
        self,
        rows: list[tuple[str, str]],
        query_embedding: list[float],
        max_distance: float | None,
    ) -> list[tuple[float, str]]:
        matches: list[tuple[float, str]] = []
        for text, raw_embedding in rows:
            entry_embedding = [float(value) for value in json.loads(raw_embedding)]
            distance = 1.0 - self._cosine_similarity(query_embedding, entry_embedding)
            if max_distance is not None and distance > max_distance:
                continue
            matches.append((distance, str(text)))
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

    def _connect_etm_store(self, path: Path) -> sqlite3.Connection:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS etm_entries (
                entry_id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
        return connection

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

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

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot_product = sum(left * right for left, right in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(value * value for value in a))
        norm_b = math.sqrt(sum(value * value for value in b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)
