from __future__ import annotations

import yaml

from engine.config import config
from engine.storage import storage


def test_session_storage_saves_and_exposes_direct_session_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")

    (tmp_path / ".overrides" / "npcs" / "mira").mkdir(parents=True)
    (tmp_path / ".overrides" / "scenes" / "cafe").mkdir(parents=True)
    (tmp_path / "scenes" / "office").mkdir(parents=True)

    storage.session.npc_id = "mira"
    storage.session.scene_id = "cafe"

    assert storage.session.npc_id == "mira"
    assert storage.session.scene_id == "cafe"
    assert yaml.safe_load((tmp_path / "session.yaml").read_text(encoding="utf-8")) == {
        "npc_id": "mira",
        "scene_id": "cafe",
    }


def test_session_storage_uses_configurable_default_ids_as_properties(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DEFAULT_NPC_ID", "nora")
    monkeypatch.setattr(config, "DEFAULT_SCENE_ID", "city_walk")
    monkeypatch.setattr(config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")

    (tmp_path / "npcs" / "nora").mkdir(parents=True)
    (tmp_path / "scenes" / "city_walk").mkdir(parents=True)

    assert storage.session.npc_id == "nora"
    assert storage.session.scene_id == "city_walk"
