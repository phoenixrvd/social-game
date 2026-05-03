from __future__ import annotations

import sqlite3
from types import SimpleNamespace

import engine.services.etm_service as etm_service_module
from engine.storage.models import Episode
from engine.storage.nodes import EtmNode
from engine.services.etm_service import EMPTY_ETM_TEXT, EtmService


def _set_embed_client(monkeypatch, embed_fn):
    monkeypatch.setattr(etm_service_module, "client", SimpleNamespace(embed_texts=embed_fn))


def test_etm_service_uses_client_embedding_fn(monkeypatch) -> None:
    def fake_embedding_fn(_text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    _set_embed_client(monkeypatch, fake_embedding_fn)
    service = EtmService()

    first = service._embed_texts("Hallo Welt")
    second = service._embed_texts("Hallo Welt")

    assert first == [0.1, 0.2, 0.3]
    assert first == second


def test_etm_service_embed_texts_trims_before_client_call(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_embedding_fn(text: str) -> list[float]:
        captured["text"] = text
        return [0.4, 0.5]

    _set_embed_client(monkeypatch, fake_embedding_fn)

    result = EtmService()._embed_texts("  Hallo  ")

    assert result == [0.4, 0.5]
    assert captured["text"] == "Hallo"


def test_etm_service_returns_empty_for_blank_input(monkeypatch) -> None:
    service = EtmService()
    _set_embed_client(
        monkeypatch,
        lambda _text: (_ for _ in ()).throw(AssertionError("should not run")),
    )

    assert service._embed_texts("   ") == []


def test_store_etm_text_persists_embedding_and_text(monkeypatch, tmp_path) -> None:
    service = EtmService()
    _set_embed_client(monkeypatch, lambda _text: [0.1, 0.2, 0.3])
    store_path = tmp_path / "etm.sqlite"
    monkey_storage = SimpleNamespace(npc=SimpleNamespace(etm=EtmNode(path=store_path)))
    monkeypatch.setattr(etm_service_module, "storage", monkey_storage)

    service._store_etm_text(" Hallo ")

    connection = sqlite3.connect(store_path)
    row = connection.execute("SELECT id, text, embedding, created_at FROM etm_entries").fetchone()
    connection.close()

    assert row is not None
    assert row[0]
    assert row[1] == "Hallo"
    assert row[2] == "[0.1, 0.2, 0.3]"
    assert row[3]


def test_query_etm_texts_filters_by_max_distance(monkeypatch, tmp_path) -> None:
    service = EtmService()
    vectors = {
        "frage": [1.0, 0.0],
        "fern": [1.0, 0.0],
        "nah": [0.0, 1.0],
    }
    _set_embed_client(monkeypatch, lambda text: vectors[text])
    store_path = tmp_path / "etm.sqlite"
    monkey_storage = SimpleNamespace(npc=SimpleNamespace(etm=EtmNode(path=store_path)))
    monkeypatch.setattr(etm_service_module, "storage", monkey_storage)

    service._store_etm_text("nah")
    service._store_etm_text("fern")
    results = service._query_etm_texts("frage")

    assert results == ["fern"]


def test_etm_node_get_returns_episode_models(tmp_path) -> None:
    node = EtmNode(path=tmp_path / "etm.sqlite")

    node.append(text="Episode A", embedding=[0.1, 0.2])
    episodes = node.get()

    assert len(episodes) == 1
    assert isinstance(episodes[0], Episode)
    assert episodes[0].text == "Episode A"
    assert episodes[0].embedding == [0.1, 0.2]
    assert episodes[0].id
    assert episodes[0].created_at


def test_episode_is_similar_uses_global_max_distance(monkeypatch) -> None:
    monkeypatch.setattr(etm_service_module.config, "ETM_RETRIEVAL_MAX_DISTANCE", 0.25)

    a = Episode(id="1", text="A", embedding=[1.0, 0.0], created_at="now")
    b = Episode(id="2", text="B", embedding=[1.0, 0.0], created_at="now")
    c = Episode(id="3", text="C", embedding=[0.0, 1.0], created_at="now")

    assert a.distance_to(b) == 0.0
    assert a.is_similar(b) is True
    assert a.is_similar(c) is False


def test_query_etm_texts_skips_blank_query_without_embedding_call(monkeypatch) -> None:
    service = EtmService()
    _set_embed_client(
        monkeypatch,
        lambda _text: (_ for _ in ()).throw(AssertionError("should not run")),
    )

    assert service._query_etm_texts("   ") == []


def test_load_relevant_skips_embedding_without_store(monkeypatch, tmp_path):
    monkeypatch.setattr(etm_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(
        EtmService,
        "_embed_texts",
        lambda _self, _text: (_ for _ in ()).throw(
            AssertionError("Ohne ETM-Speicher darf kein Embedding-Call erfolgen")
        ),
    )

    result = EtmService().load_relevant("Hallo")

    assert result == EMPTY_ETM_TEXT


def test_load_relevant_skips_embedding_for_empty_query(monkeypatch):
    monkeypatch.setattr(
        EtmService,
        "_embed_texts",
        lambda _self, _text: (_ for _ in ()).throw(AssertionError("Ohne Query darf kein Embedding-Call erfolgen")),
    )

    result = EtmService().load_relevant("   ")

    assert result == EMPTY_ETM_TEXT


def test_load_relevant_returns_formatted_matches(monkeypatch, tmp_path):
    store_path = tmp_path / ".data" / "npcs" / "vika" / "office" / "etm.sqlite"
    store_path.parent.mkdir(parents=True)
    store_path.touch()

    def fake_query(self, query_text: str) -> list[str]:
        assert query_text == "Wollen wir wieder in eine Bar gehen?"
        return [
            "Er erinnert sich an eine ruhige Bar mit guten Gläsern.",
            "Kennt den Spieler",
        ]

    monkeypatch.setattr(etm_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(EtmService, "_query_etm_texts", fake_query)


    result = EtmService().load_relevant("Wollen wir wieder in eine Bar gehen?")

    assert result == "- Er erinnert sich an eine ruhige Bar mit guten Gläsern.\n- Kennt den Spieler"