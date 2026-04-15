from __future__ import annotations

import engine.storage as storage_module
import engine.stores.session_store as session_store_module
from engine.models import Session


class FakeSessionStore:
    def load(self) -> Session:
        return Session(npc_id="vika", scene_id="office")


def test_storage_npc_and_scene_use_session_and_priority(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_module.config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(storage_module.config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(storage_module.config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(storage_module.config, "DATA_DIR", tmp_path / ".data")
    monkeypatch.setattr(storage_module.config, "OVERRIDES_DIR", tmp_path / ".overrides")
    monkeypatch.setattr(storage_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(storage_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(session_store_module, "SessionStore", FakeSessionStore)

    (tmp_path / "npcs" / "vika").mkdir(parents=True)
    (tmp_path / "npcs" / "vika" / "state.md").write_text("default", encoding="utf-8")
    (tmp_path / ".overrides" / "npcs" / "vika").mkdir(parents=True)
    (tmp_path / ".overrides" / "npcs" / "vika" / "state.md").write_text("override", encoding="utf-8")
    (tmp_path / ".data" / "npcs" / "vika" / "office").mkdir(parents=True)
    (tmp_path / ".data" / "npcs" / "vika" / "office" / "state.md").write_text("runtime", encoding="utf-8")

    (tmp_path / "scenes" / "office").mkdir(parents=True)
    (tmp_path / "scenes" / "office" / "scene.md").write_text("default-scene", encoding="utf-8")
    (tmp_path / ".overrides" / "scenes" / "office").mkdir(parents=True)
    (tmp_path / ".overrides" / "scenes" / "office" / "scene.md").write_text("override-scene", encoding="utf-8")
    (tmp_path / ".data" / "npcs" / "vika" / "office" / "scene.md").write_text("runtime-scene", encoding="utf-8")

    assert storage_module.storage.npc.state.name == "state.md"
    assert storage_module.storage.npc.state.path == tmp_path / ".data" / "npcs" / "vika" / "office" / "state.md"
    assert storage_module.storage.npc.state_original.path == tmp_path / ".overrides" / "npcs" / "vika" / "state.md"
    assert storage_module.storage.npc.state.get() == "runtime"

    assert storage_module.storage.scene.scene.path == tmp_path / ".data" / "npcs" / "vika" / "office" / "scene.md"
    assert storage_module.storage.scene.scene_original.path == tmp_path / ".overrides" / "scenes" / "office" / "scene.md"
    assert storage_module.storage.scene.scene.get() == "runtime-scene"


def test_storage_base_paths_exposed(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_module.config, "DATA_DIR", tmp_path / ".data")
    monkeypatch.setattr(storage_module.config, "OVERRIDES_DIR", tmp_path / ".overrides")

    assert storage_module.storage.data == tmp_path / ".data"
    assert storage_module.storage.etm_fastembed_cache == tmp_path / ".data" / "fastembed_cache"
    assert storage_module.storage.overrides_root == tmp_path / ".overrides"

