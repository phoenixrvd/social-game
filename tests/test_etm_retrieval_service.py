from pathlib import Path

import engine.services.etm_service as etm_service_module
from engine.services.etm_service import EMPTY_ETM_TEXT, EtmService


def test_load_relevant_skips_embedding_without_store(monkeypatch, tmp_path):
    monkeypatch.setattr(etm_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(
        etm_service_module.client,
        "embed_texts",
        lambda _texts: (_ for _ in ()).throw(AssertionError("Ohne ETM-Speicher darf kein Embedding-Call erfolgen")),
    )

    result = EtmService().load_relevant("Hallo")

    assert result == EMPTY_ETM_TEXT


def test_load_relevant_skips_embedding_for_empty_query(monkeypatch):
    monkeypatch.setattr(
        etm_service_module.client,
        "embed_texts",
        lambda _texts: (_ for _ in ()).throw(AssertionError("Ohne Query darf kein Embedding-Call erfolgen")),
    )

    result = EtmService().load_relevant("   ")

    assert result == EMPTY_ETM_TEXT


def test_load_relevant_uses_top_k_and_max_distance(monkeypatch, tmp_path):
    store_path = tmp_path / ".data" / "npcs" / "vika" / "office" / "etm.chroma"
    store_path.mkdir(parents=True)

    class FakeEtmVectorStore:
        def __init__(self, path: Path) -> None:
            assert path == store_path

        def query(self, embedding: list[float], top_k: int, max_distance: float) -> list[str]:
            assert embedding == [0.1, 0.2, 0.3]
            assert top_k == 4
            assert max_distance == etm_service_module.config.ETM_RETRIEVAL_MAX_DISTANCE
            return [
                "Er erinnert sich an eine ruhige Bar mit guten Gläsern.",
                "Kennt den Spieler",
            ]

    monkeypatch.setattr(etm_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(etm_service_module.client, "embed_texts", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(etm_service_module, "EtmVectorStore", FakeEtmVectorStore)

    # Make storage bootstrap deterministic for this test run.
    import engine.storage as storage_module
    from engine.models import Session

    monkeypatch.setattr(storage_module.storage, "_session", staticmethod(lambda: Session(npc_id="vika", scene_id="office")))
    storage_module.storage._npc_view = None
    storage_module.storage._scene_view = None

    result = EtmService().load_relevant("Wollen wir wieder in eine Bar gehen?")

    assert result == "- Er erinnert sich an eine ruhige Bar mit guten Gläsern.\n- Kennt den Spieler"
