from pathlib import Path

import engine.services.etm_retrieval_service as etm_retrieval_service_module
from engine.models import Npc, Scene
from engine.services.etm_retrieval_service import EMPTY_ETM_TEXT, EtmRetrievalService


def _npc() -> Npc:
    return Npc(
        npc_id="vika",
        description="desc",
        system_prompt="sys",
        state="mood: neutral",
        character={"name": "Vika"},
        relationship="Kennt den Spieler",
        scene=Scene(scene_id="office", description="Szene"),
        stm=[],
    )


def test_load_relevant_skips_embedding_without_store(monkeypatch, tmp_path):
    monkeypatch.setattr(etm_retrieval_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(
        etm_retrieval_service_module,
        "embed_texts",
        lambda _texts: (_ for _ in ()).throw(AssertionError("Ohne ETM-Speicher darf kein Embedding-Call erfolgen")),
    )

    result = EtmRetrievalService().load_relevant(_npc(), "Hallo")

    assert result == EMPTY_ETM_TEXT


def test_load_relevant_skips_embedding_for_empty_query(monkeypatch):
    monkeypatch.setattr(
        etm_retrieval_service_module,
        "embed_texts",
        lambda _texts: (_ for _ in ()).throw(AssertionError("Ohne Query darf kein Embedding-Call erfolgen")),
    )

    result = EtmRetrievalService().load_relevant(_npc(), "   ")

    assert result == EMPTY_ETM_TEXT


def test_load_relevant_uses_top_k_and_max_distance(monkeypatch, tmp_path):
    npc = _npc()
    store_path = tmp_path / ".data" / "npcs" / "vika" / "office" / "etm.chroma"
    store_path.mkdir(parents=True)

    class FakeEtmVectorStore:
        def __init__(self, path: Path) -> None:
            assert path == store_path

        def query(self, embedding: list[float], top_k: int, max_distance: float) -> list[str]:
            assert embedding == [0.1, 0.2, 0.3]
            assert top_k == 4
            assert max_distance == etm_retrieval_service_module.config.ETM_RETRIEVAL_MAX_DISTANCE
            return [
                "Er erinnert sich an eine ruhige Bar mit guten Gläsern.",
                "Kennt den Spieler",
            ]

    monkeypatch.setattr(etm_retrieval_service_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(etm_retrieval_service_module, "embed_texts", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(etm_retrieval_service_module, "EtmVectorStore", FakeEtmVectorStore)

    result = EtmRetrievalService().load_relevant(npc, "Wollen wir wieder in eine Bar gehen?")

    assert result == "- Er erinnert sich an eine ruhige Bar mit guten Gläsern.\n- Kennt den Spieler"
