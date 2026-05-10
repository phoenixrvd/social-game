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


def test_prompt_image_style_rules_prefers_override_over_default(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config, "OVERRIDES_PROMPTS_DIR", tmp_path / ".overrides" / "prompts")

    default_prompt = tmp_path / "prompts" / "image_style_rules.md"
    default_prompt.parent.mkdir(parents=True, exist_ok=True)
    default_prompt.write_text("default-style", encoding="utf-8")

    override_prompt = tmp_path / ".overrides" / "prompts" / "image_style_rules.md"
    override_prompt.parent.mkdir(parents=True, exist_ok=True)
    override_prompt.write_text("override-style", encoding="utf-8")

    item = storage.prompts.image_style_rules
    assert item.path == override_prompt
    assert item.get() == "override-style"


def test_prompt_npc_scene_create_text_prefers_override_over_default(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config, "OVERRIDES_PROMPTS_DIR", tmp_path / ".overrides" / "prompts")

    default_prompt = tmp_path / "prompts" / "npc_scene_create_text.md"
    default_prompt.parent.mkdir(parents=True, exist_ok=True)
    default_prompt.write_text("default-npc-scene", encoding="utf-8")

    override_prompt = tmp_path / ".overrides" / "prompts" / "npc_scene_create_text.md"
    override_prompt.parent.mkdir(parents=True, exist_ok=True)
    override_prompt.write_text("override-npc-scene", encoding="utf-8")

    item = storage.prompts.npc_scene_create_text
    assert item.path == override_prompt
    assert item.get() == "override-npc-scene"


def test_prompt_npc_create_description_prefers_override_over_default(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config, "OVERRIDES_PROMPTS_DIR", tmp_path / ".overrides" / "prompts")

    default_prompt = tmp_path / "prompts" / "npc_create_description.md"
    default_prompt.parent.mkdir(parents=True, exist_ok=True)
    default_prompt.write_text("default-npc-description", encoding="utf-8")

    override_prompt = tmp_path / ".overrides" / "prompts" / "npc_create_description.md"
    override_prompt.parent.mkdir(parents=True, exist_ok=True)
    override_prompt.write_text("override-npc-description", encoding="utf-8")

    item = storage.prompts.npc_create_description
    assert item.path == override_prompt
    assert item.get() == "override-npc-description"


def test_prompt_npc_create_state_prefers_override_over_default(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config, "OVERRIDES_PROMPTS_DIR", tmp_path / ".overrides" / "prompts")

    default_prompt = tmp_path / "prompts" / "npc_create_state.md"
    default_prompt.parent.mkdir(parents=True, exist_ok=True)
    default_prompt.write_text("default-npc-state", encoding="utf-8")

    override_prompt = tmp_path / ".overrides" / "prompts" / "npc_create_state.md"
    override_prompt.parent.mkdir(parents=True, exist_ok=True)
    override_prompt.write_text("override-npc-state", encoding="utf-8")

    item = storage.prompts.npc_create_state
    assert item.path == override_prompt
    assert item.get() == "override-npc-state"


def test_prompt_npc_create_image_prefers_override_over_default(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config, "OVERRIDES_PROMPTS_DIR", tmp_path / ".overrides" / "prompts")

    default_prompt = tmp_path / "prompts" / "npc_create_image.md"
    default_prompt.parent.mkdir(parents=True, exist_ok=True)
    default_prompt.write_text("default-npc-image", encoding="utf-8")

    override_prompt = tmp_path / ".overrides" / "prompts" / "npc_create_image.md"
    override_prompt.parent.mkdir(parents=True, exist_ok=True)
    override_prompt.write_text("override-npc-image", encoding="utf-8")

    item = storage.prompts.npc_create_image
    assert item.path == override_prompt
    assert item.get() == "override-npc-image"


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


def test_storage_npc_video_prefers_override_over_default(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    _set_session(tmp_path, "vika", "office")
    (tmp_path / "scenes" / "office").mkdir(parents=True)

    default_video = tmp_path / "npcs" / "vika" / "video.mp4"
    default_video.parent.mkdir(parents=True)
    default_video.write_bytes(b"default")

    override_video = tmp_path / ".overrides" / "npcs" / "vika" / "video.mp4"
    override_video.parent.mkdir(parents=True)
    override_video.write_bytes(b"override")

    assert storage.npc.video.path == override_video
    assert storage.npc.video.get() == override_video


def test_storage_npc_img_backup_returns_image_files_newest_first(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    _set_session(tmp_path, "vika", "office")

    backup_dir = tmp_path / ".data" / "npcs" / "vika" / "office" / "img_backup"
    backup_dir.mkdir(parents=True)
    (backup_dir / "img-20260510-100000.png").write_bytes(b"older")
    (backup_dir / "img-20260510-110000.png").write_bytes(b"newer")
    (backup_dir / "note.txt").write_text("ignored", encoding="utf-8")

    backups = storage.npc.img_backup

    assert [image.name for image in backups] == ["img-20260510-110000.png", "img-20260510-100000.png"]
    assert [image.get() for image in backups] == [
        backup_dir / "img-20260510-110000.png",
        backup_dir / "img-20260510-100000.png",
    ]
