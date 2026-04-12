from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import chromadb

_COLLECTION_NAME = "etm"


class EtmVectorStore:
    def __init__(self, path: Path) -> None:
        self._fallback_path = path / "records.json"
        path.mkdir(parents=True, exist_ok=True)
        try:
            self._client = chromadb.PersistentClient(path=str(path))
            self._collection = self._client.get_or_create_collection(
                name=_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            self._fallback = False
        except chromadb.errors.ChromaError:
            self._client = None
            self._collection = None
            self._fallback = True

    def add(self, text: str, embedding: list[float], entry_id: str) -> None:
        if self._fallback:
            self._add_fallback(text, embedding, entry_id)
            return

        if self._collection is None:
            raise RuntimeError("ETM vector store collection is not initialized")

        self._collection.add(
            ids=[entry_id],
            documents=[text],
            embeddings=[embedding],
        )

    def query(self, embedding: list[float], top_k: int, max_distance: float | None = None) -> list[str]:
        if self._fallback:
            return self._query_fallback(embedding, top_k, max_distance)

        if self._collection is None:
            raise RuntimeError("ETM vector store collection is not initialized")

        count = self._collection.count()
        if count == 0:
            return []
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, count),
            include=["documents", "distances"],
        )
        docs = results.get("documents") or []
        distances = results.get("distances") or []
        if not docs:
            return []

        return self._filter_by_distance(docs[0], distances[0] if distances else [], max_distance)

    def _add_fallback(self, text: str, embedding: list[float], entry_id: str) -> None:
        records = self._load_fallback_records()
        records.append({"id": entry_id, "text": text, "embedding": embedding})
        self._save_fallback_records(records)

    def _query_fallback(self, embedding: list[float], top_k: int, max_distance: float | None) -> list[str]:
        records = self._load_fallback_records()
        ranked = sorted(
            records,
            key=lambda row: self._cosine_similarity(embedding, row["embedding"]),
            reverse=True,
        )
        docs = [str(row["text"]) for row in ranked[:top_k]]
        distances = [1.0 - self._cosine_similarity(embedding, row["embedding"]) for row in ranked[:top_k]]
        return self._filter_by_distance(docs, distances, max_distance)

    def _load_fallback_records(self) -> list[dict[str, Any]]:
        if not self._fallback_path.exists():
            return []

        rows = json.loads(self._fallback_path.read_text(encoding="utf-8"))
        return rows if isinstance(rows, list) else []

    def _save_fallback_records(self, records: list[dict[str, Any]]) -> None:
        self._fallback_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(left * right for left, right in zip(a, b))
        a_norm = math.sqrt(sum(value * value for value in a))
        b_norm = math.sqrt(sum(value * value for value in b))
        if a_norm == 0 or b_norm == 0:
            return 0.0
        return dot / (a_norm * b_norm)

    @staticmethod
    def _filter_by_distance(docs: list[str], distances: list[float], max_distance: float | None) -> list[str]:
        if max_distance is None:
            return docs

        return [doc for doc, distance in zip(docs, distances, strict=False) if distance <= max_distance]
