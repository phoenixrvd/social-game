from __future__ import annotations

import yaml

import engine.storage as storage_module


def test_session_storage_saves_and_exposes_direct_session_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_module.config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(storage_module.config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(storage_module.config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(storage_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(storage_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")

    (tmp_path / ".overrides" / "npcs" / "mira").mkdir(parents=True)
    (tmp_path / ".overrides" / "scenes" / "cafe").mkdir(parents=True)

    saved = storage_module.storage.session.save(npc_id="mira", scene_id="cafe").get()

    assert saved.npc_id == "mira"
    assert saved.scene_id == "cafe"
    assert storage_module.storage.session.get().npc_id == "mira"
    assert storage_module.storage.session.get().scene_id == "cafe"
    assert yaml.safe_load((tmp_path / "session.yaml").read_text(encoding="utf-8")) == {
        "npc_id": "mira",
        "scene_id": "cafe",
    }


def test_session_storage_uses_configurable_default_ids_as_properties(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_module.config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(storage_module.config, "DEFAULT_NPC_ID", "nora")
    monkeypatch.setattr(storage_module.config, "DEFAULT_SCENE_ID", "city_walk")

    assert storage_module.storage.session.get().npc_id == "nora"
    assert storage_module.storage.session.get().scene_id == "city_walk"
