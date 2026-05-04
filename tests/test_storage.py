from __future__ import annotations

from engine.config import config
from engine.storage import storage


def _set_session(tmp_path, npc_id: str, scene_id: str) -> None:
    (tmp_path / "session.yaml").write_text(
        f"npc_id: {npc_id}\nscene_id: {scene_id}\n",
        encoding="utf-8",
    )


def test_storage_npc_and_scene_use_session_and_priority(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / ".data")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    _set_session(tmp_path, "vika", "office")

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

    assert storage.npc.state_runtime.path == tmp_path / ".data" / "npcs" / "vika" / "office" / "state.md"
    assert storage.npc.state_original.path == tmp_path / ".overrides" / "npcs" / "vika" / "state.md"
    assert storage.npc.state == "runtime"

    assert storage.scene.scene.path == tmp_path / ".data" / "npcs" / "vika" / "office" / "scene.md"
    assert storage.scene.scene_original.path == tmp_path / ".overrides" / "scenes" / "office" / "scene.md"
    assert storage.scene.scene.get() == "runtime-scene"


def test_storage_base_paths_exposed(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / ".data")

    assert storage.data == tmp_path / ".data"


def test_prompt_image_refresh_prefers_override_over_default(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config, "OVERRIDES_PROMPTS_DIR", tmp_path / ".overrides" / "prompts")

    default_prompt = tmp_path / "prompts" / "image_refresh.md"
    default_prompt.parent.mkdir(parents=True, exist_ok=True)
    default_prompt.write_text("default", encoding="utf-8")

    override_prompt = tmp_path / ".overrides" / "prompts" / "image_refresh.md"
    override_prompt.parent.mkdir(parents=True, exist_ok=True)
    override_prompt.write_text("override", encoding="utf-8")

    item = storage.prompts.image_refresh
    assert item.path == override_prompt
    assert item.get() == "override"


def test_storage_falls_back_to_default_npc_and_scene_files(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "DEFAULT_NPC_ID", "vika")
    monkeypatch.setattr(config, "DEFAULT_SCENE_ID", "office")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    _set_session(tmp_path, "new_npc", "new_scene")

    (tmp_path / "npcs" / "new_npc").mkdir(parents=True)
    (tmp_path / "npcs" / "vika").mkdir(parents=True)
    (tmp_path / "npcs" / "vika" / "state.md").write_text("default-npc-state", encoding="utf-8")

    (tmp_path / "scenes" / "new_scene").mkdir(parents=True)
    (tmp_path / "scenes" / "office").mkdir(parents=True)
    (tmp_path / "scenes" / "office" / "scene.md").write_text("default-scene", encoding="utf-8")

    assert storage.npc.state_original.path == tmp_path / "npcs" / "vika" / "state.md"
    assert storage.npc.state == "default-npc-state"
    assert storage.scene.scene.path == tmp_path / "scenes" / "office" / "scene.md"
    assert storage.scene.scene.get() == "default-scene"


def test_storage_description_uses_default_path_when_runtime_file_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    _set_session(tmp_path, "vika", "office")
    (tmp_path / "scenes" / "office").mkdir(parents=True)

    npc_dir = tmp_path / "npcs" / "vika"
    npc_dir.mkdir(parents=True)
    (npc_dir / "description.md").write_text("default-description", encoding="utf-8")

    runtime_dir = tmp_path / ".data" / "npcs" / "vika" / "office"
    runtime_dir.mkdir(parents=True)
    assert storage.npc.description.path == npc_dir / "description.md"
    assert storage.npc.description.get() == "default-description"

