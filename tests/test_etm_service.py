from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import engine.storage as storage_module
import engine.services.etm_service as etm_service_module
from engine.services.etm_service import EMPTY_ETM_TEXT, EtmService


def test_etm_service_uses_local_embedding_fn() -> None:
    def fake_embedding_fn(_texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3]]

    service = EtmService()
    service._local_embedding_fn = fake_embedding_fn

    first = service._embed_texts(["Hallo Welt"])[0]
    second = service._embed_texts(["Hallo Welt"])[0]
    assert first == [0.1, 0.2, 0.3]
    assert first == second


def test_etm_service_uses_data_cache_dir(monkeypatch, tmp_path) -> None:
    captured: dict[str, str] = {}

    class FakeTextEmbedding:
        def __init__(self, *, model_name, cache_dir):
            captured["model_name"] = model_name
            captured["cache_dir"] = cache_dir

        @staticmethod
        def embed(_texts: list[str]) -> list[list[float]]:
            return [[0.4, 0.5]]

    class FakeStorage:
        @property
        def etm_fastembed_cache(self):
            return tmp_path / "fastembed_cache"

    monkeypatch.setitem(sys.modules, "fastembed", SimpleNamespace(TextEmbedding=FakeTextEmbedding))
    monkeypatch.setattr(etm_service_module, "storage", FakeStorage())

    service = EtmService()
    assert service._embed_texts(["Hallo"]) == [[0.4, 0.5]]
    assert captured["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert captured["cache_dir"] == str(tmp_path / "fastembed_cache")


def test_etm_service_returns_empty_for_blank_inputs() -> None:
    service = EtmService()
    service._local_embedding_fn = lambda _texts: (_ for _ in ()).throw(AssertionError("should not run"))

    assert service._embed_texts(["", "   "]) == []


def test_store_etm_text_persists_embedding_and_text(tmp_path) -> None:
    service = EtmService()
    service._local_embedding_fn = lambda _texts: [[0.1, 0.2, 0.3]]
    store_path = tmp_path / "etm.sqlite"

    service._store_etm_text(store_path, " Hallo ")

    connection = sqlite3.connect(store_path)
    row = connection.execute("SELECT entry_id, text, embedding, created_at FROM etm_entries").fetchone()
    connection.close()

    assert row is not None
    assert row[0]
    assert row[1] == "Hallo"
    assert row[2] == "[0.1, 0.2, 0.3]"
    assert row[3]


def test_query_etm_texts_filters_by_max_distance(tmp_path) -> None:
    service = EtmService()
    vectors = {
        "frage": [1.0, 0.0],
        "fern": [1.0, 0.0],
        "nah": [0.0, 1.0],
    }
    service._local_embedding_fn = lambda texts: [vectors[text] for text in texts]
    store_path = tmp_path / "etm.sqlite"

    service._store_etm_text(store_path, "nah")
    service._store_etm_text(store_path, "fern")

    results = service._query_etm_texts(store_path, "frage")

    assert results == ["fern"]


def test_query_etm_texts_skips_blank_query_without_embedding_call(tmp_path) -> None:
    service = EtmService()
    service._local_embedding_fn = lambda _texts: (_ for _ in ()).throw(AssertionError("should not run"))

    assert service._query_etm_texts(tmp_path / "etm.sqlite", "   ") == []


def test_load_relevant_skips_embedding_without_store(monkeypatch, tmp_path):
    monkeypatch.setattr(etm_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(
        EtmService,
        "_embed_texts",
        lambda _self, _texts: (_ for _ in ()).throw(
            AssertionError("Ohne ETM-Speicher darf kein Embedding-Call erfolgen")
        ),
    )

    result = EtmService().load_relevant("Hallo")

    assert result == EMPTY_ETM_TEXT


def test_load_relevant_skips_embedding_for_empty_query(monkeypatch):
    monkeypatch.setattr(
        EtmService,
        "_embed_texts",
        lambda _self, _texts: (_ for _ in ()).throw(AssertionError("Ohne Query darf kein Embedding-Call erfolgen")),
    )

    result = EtmService().load_relevant("   ")

    assert result == EMPTY_ETM_TEXT


def test_load_relevant_returns_formatted_matches(monkeypatch, tmp_path):
    store_path = tmp_path / ".data" / "npcs" / "vika" / "office" / "etm.sqlite"
    store_path.parent.mkdir(parents=True)
    store_path.touch()

    def fake_query(self, path: Path, query_text: str) -> list[str]:
        assert path == store_path
        assert query_text == "Wollen wir wieder in eine Bar gehen?"
        return [
            "Er erinnert sich an eine ruhige Bar mit guten Gläsern.",
            "Kennt den Spieler",
        ]

    monkeypatch.setattr(etm_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(EtmService, "_query_etm_texts", fake_query)

    # Make storage bootstrap deterministic for this test run.
    monkeypatch.setattr(
        storage_module.SessionStorageItem,
        "get",
        lambda _self: SimpleNamespace(npc_id="vika", scene_id="office"),
    )

    result = EtmService().load_relevant("Wollen wir wieder in eine Bar gehen?")

    assert result == "- Er erinnert sich an eine ruhige Bar mit guten Gläsern.\n- Kennt den Spieler"