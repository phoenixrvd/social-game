from pathlib import Path

from chromadb import errors as chroma_errors

from engine.stores.etm_vector_store import EtmVectorStore


def _store(tmp_path: Path) -> EtmVectorStore:
    return EtmVectorStore(tmp_path / "etm.chroma")


def _embedding(seed: float, dims: int = 8) -> list[float]:
    base = [seed + i * 0.01 for i in range(dims)]
    norm = sum(x * x for x in base) ** 0.5
    return [x / norm for x in base]


def test_add_and_query_returns_stored_text(tmp_path):
    store = _store(tmp_path)
    emb = _embedding(0.5)

    store.add("Vika vertraut dem Spieler mehr.", emb, "id-1")
    results = store.query(emb, top_k=1)

    assert results == ["Vika vertraut dem Spieler mehr."]


def test_query_empty_store_returns_empty_list(tmp_path):
    store = _store(tmp_path)
    results = store.query(_embedding(0.3), top_k=5)

    assert results == []


def test_query_top_k_limits_results(tmp_path):
    store = _store(tmp_path)

    for i in range(5):
        store.add(f"eintrag-{i}", _embedding(i * 0.1), f"id-{i}")

    results = store.query(_embedding(0.2), top_k=2)

    assert len(results) == 2


def test_multiple_adds_are_all_queryable(tmp_path):
    store = _store(tmp_path)

    store.add("Beziehung hat sich vertieft.", _embedding(0.1), "id-a")
    store.add("Sie mag keine Konfrontation.", _embedding(0.9), "id-b")

    results = store.query(_embedding(0.1), top_k=5)

    assert len(results) == 2


def test_query_filters_by_max_distance(tmp_path):
    store = _store(tmp_path)

    store.add("Naher Treffer.", [1.0, 0.0], "id-a")
    store.add("Ferner Treffer.", [0.0, 1.0], "id-b")

    results = store.query([1.0, 0.0], top_k=5, max_distance=0.35)

    assert results == ["Naher Treffer."]


def test_query_resets_store_on_dimension_mismatch(tmp_path, monkeypatch):
    store = _store(tmp_path)
    events: list[str] = []

    class FakeCollection:
        @staticmethod
        def count() -> int:
            return 1

        @staticmethod
        def query(**_kwargs):
            raise chroma_errors.InvalidArgumentError("Collection expecting embedding with dimension of 1536, got 384")

    monkeypatch.setattr(store, "_collection", FakeCollection())
    monkeypatch.setattr(store, "_reset_store", lambda: events.append("reset"))

    assert store.query(_embedding(0.2), top_k=2) == []
    assert events == ["reset"]


def test_add_resets_store_and_retries_on_dimension_mismatch(tmp_path, monkeypatch):
    store = _store(tmp_path)
    events: list[str] = []
    captured: dict[str, list[object]] = {}

    class FailingCollection:
        @staticmethod
        def add(**_kwargs):
            raise chroma_errors.InvalidArgumentError("Collection expecting embedding with dimension of 1536, got 384")

    class RecoveredCollection:
        @staticmethod
        def add(*, ids, documents, embeddings):
            captured["ids"] = ids
            captured["documents"] = documents
            captured["embeddings"] = embeddings

    def fake_reset_store() -> None:
        events.append("reset")
        store._collection = RecoveredCollection()
        store._fallback = False

    monkeypatch.setattr(store, "_collection", FailingCollection())
    monkeypatch.setattr(store, "_reset_store", fake_reset_store)

    store.add("Neue Episode", [0.1, 0.2], "id-1")

    assert events == ["reset"]
    assert captured == {
        "ids": ["id-1"],
        "documents": ["Neue Episode"],
        "embeddings": [[0.1, 0.2]],
    }


