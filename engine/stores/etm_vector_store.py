from __future__ import annotations

import math
from pathlib import Path

import chromadb
from chromadb import Collection

_COLLECTION_NAME = "etm"


class EtmVectorStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._client: chromadb.PersistentClient | None = None
        self._collection: Collection | None = None
        self._initialize_backend()

    def add(self, text: str, embedding: list[float], entry_id: str) -> None:
        self._insert_into_collection(text, embedding, entry_id)

    def query(self, embedding: list[float], top_k: int, max_distance: float | None = None) -> list[str]:
        if top_k <= 0:
            return []

        return self._query_collection(embedding, top_k, max_distance)

    def _initialize_backend(self) -> None:
        self._path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self._path))
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _insert_into_collection(self, text: str, embedding: list[float], entry_id: str) -> None:
        self._require_collection().add(
            ids=[entry_id],
            documents=[text],
            embeddings=[embedding],
        )

    def _query_collection(self, embedding: list[float], top_k: int, max_distance: float | None) -> list[str]:
        collection = self._require_collection()
        count = collection.count()
        if count == 0:
            return []

        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, count),
            include=["documents", "distances"],
        )

        documents = results.get("documents") or []
        distances = results.get("distances") or []
        if not documents:
            return []

        docs = [str(document) for document in documents[0]]
        dists = [float(distance) for distance in distances[0]] if distances else []
        return self._filter_by_distance(docs, dists, max_distance)

    def _require_collection(self) -> Collection:
        if self._collection is None:
            raise RuntimeError("ETM vector store collection is not initialized")
        return self._collection

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot_product = sum(left * right for left, right in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(value * value for value in a))
        norm_b = math.sqrt(sum(value * value for value in b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    @staticmethod
    def _filter_by_distance(docs: list[str], distances: list[float], max_distance: float | None) -> list[str]:
        if max_distance is None:
            return docs

        return [
            doc
            for doc, distance in zip(docs, distances, strict=False)
            if distance <= max_distance
        ]
