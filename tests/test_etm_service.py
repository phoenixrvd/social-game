from __future__ import annotations

from types import SimpleNamespace

import engine.services.etm_service as etm_service_module
from engine.services.etm_service import EMPTY_ETM_TEXT, EtmService


class FakeLightRagMemory:
    inserted: list[str] = []
    queries: list[tuple[str, int]] = []
    context = ""

    def __init__(self, working_dir):
        self.working_dir = working_dir

    def insert(self, text: str) -> None:
        self.inserted.append(text)

    def query_context(self, query: str, top_k: int) -> str:
        self.queries.append((query, top_k))
        return self.context


def _use_fake_memory(monkeypatch, tmp_path):
    FakeLightRagMemory.inserted = []
    FakeLightRagMemory.queries = []
    FakeLightRagMemory.context = ""
    fake_storage = SimpleNamespace(npc=SimpleNamespace(etm_dir=tmp_path / "etm_lightrag"))
    monkeypatch.setattr(etm_service_module, "storage", fake_storage)
    monkeypatch.setattr(etm_service_module, "LightRagMemory", FakeLightRagMemory)


def test_store_etm_text_inserts_cleaned_text_into_lightrag(monkeypatch, tmp_path) -> None:
    _use_fake_memory(monkeypatch, tmp_path)

    EtmService()._store_etm_text(" Hallo ")

    assert FakeLightRagMemory.inserted == ["Hallo"]


def test_store_etm_text_skips_blank_text(monkeypatch, tmp_path) -> None:
    _use_fake_memory(monkeypatch, tmp_path)

    EtmService()._store_etm_text("   ")

    assert FakeLightRagMemory.inserted == []


def test_query_etm_text_uses_lightrag_context(monkeypatch, tmp_path) -> None:
    _use_fake_memory(monkeypatch, tmp_path)
    FakeLightRagMemory.context = "relevanter Kontext"
    monkeypatch.setattr(etm_service_module.config, "ETM_RETRIEVAL_TOP_K", 2)

    result = EtmService()._query_etm_text("frage")

    assert result == "relevanter Kontext"
    assert FakeLightRagMemory.queries == [("frage", 2)]


def test_query_etm_text_returns_empty_for_empty_lightrag_context(monkeypatch, tmp_path) -> None:
    _use_fake_memory(monkeypatch, tmp_path)

    assert EtmService()._query_etm_text("frage") == ""


def test_load_relevant_returns_empty_placeholder_without_matches(monkeypatch, tmp_path) -> None:
    _use_fake_memory(monkeypatch, tmp_path)

    result = EtmService().load_relevant("Hallo")

    assert result == EMPTY_ETM_TEXT


def test_load_relevant_returns_formatted_lightrag_context(monkeypatch, tmp_path) -> None:
    _use_fake_memory(monkeypatch, tmp_path)
    FakeLightRagMemory.context = "Er erinnert sich an eine ruhige Bar."

    result = EtmService().load_relevant("Wollen wir wieder in eine Bar gehen?")

    assert result == "Er erinnert sich an eine ruhige Bar."
