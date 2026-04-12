from __future__ import annotations

import engine.stores.session_store as session_store_module


def test_session_store_accepts_npc_and_scene_from_overrides(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store_module.config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(session_store_module.config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(session_store_module.config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(session_store_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(session_store_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")

    (tmp_path / ".overrides" / "npcs" / "mira").mkdir(parents=True)
    (tmp_path / ".overrides" / "scenes" / "cafe").mkdir(parents=True)

    store = session_store_module.SessionStore()
    session = store.save(npc="mira", scene="cafe")

    assert session.npc_id == "mira"
    assert session.scene_id == "cafe"

