from __future__ import annotations

from engine.config import config
from engine.storage import storage
from engine.storage.paths import path_resolver


def test_storage_lists_union_of_overrides_and_default(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")

    (tmp_path / "npcs" / "vika").mkdir(parents=True)
    (tmp_path / ".overrides" / "npcs" / "mira").mkdir(parents=True)
    (tmp_path / "scenes" / "office").mkdir(parents=True)
    (tmp_path / ".overrides" / "scenes" / "cafe").mkdir(parents=True)

    assert [npc_view.npc_id for npc_view in storage.list_npcs] == ["mira", "vika"]
    assert [scene_view.scene_id for scene_view in storage.list_scenes] == ["cafe", "office"]


def test_storage_prefers_first_existing_file(tmp_path):
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    second.write_text("ok", encoding="utf-8")

    resolved = path_resolver.preferred_file((first, second))
    assert resolved == second



