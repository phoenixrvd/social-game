import pytest
import yaml

from engine.services.id_normalizer import normalize_to_snake_id
from engine.services.npc_service import NpcService
from engine.services.scene_service import SceneService


def test_normalize_to_snake_id_converts_name():
    assert normalize_to_snake_id("Anna Maria!!!") == "anna_maria"


def test_normalize_to_snake_id_returns_empty_for_invalid_name():
    assert normalize_to_snake_id("@@@") == ""


def test_npc_service_create_override_creates_character_yaml_only(tmp_path, monkeypatch):
    import engine.services.npc_service as npc_module

    monkeypatch.setattr(npc_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")

    target_dir = NpcService().create_override("alex")

    assert yaml.safe_load((target_dir / "character.yaml").read_text(encoding="utf-8")) == {"name": "alex"}
    assert not (target_dir / "description.md").exists()
    assert not (target_dir / "scene.md").exists()


def test_npc_service_create_override_is_idempotent_when_target_exists(tmp_path, monkeypatch):
    import engine.services.npc_service as npc_module

    monkeypatch.setattr(npc_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")

    existing_target = tmp_path / ".overrides" / "npcs" / "alex"
    existing_target.mkdir(parents=True)
    (existing_target / "character.yaml").write_text("name: Bestehend\n", encoding="utf-8")

    target_dir = NpcService().create_override("alex")

    assert target_dir == existing_target
    assert (existing_target / "character.yaml").read_text(encoding="utf-8") == "name: Bestehend\n"


def test_npc_service_create_override_normalizes_name_to_snake_case(tmp_path, monkeypatch):
    import engine.services.npc_service as npc_module

    monkeypatch.setattr(npc_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")

    target_dir = NpcService().create_override("Anna Maria!!!")

    assert target_dir.name == "anna_maria"
    assert (target_dir / "character.yaml").is_file()
    assert yaml.safe_load((target_dir / "character.yaml").read_text(encoding="utf-8")) == {
        "name": "Anna Maria!!!"
    }


def test_npc_service_create_override_rejects_invalid_name(tmp_path, monkeypatch):
    import engine.services.npc_service as npc_module

    monkeypatch.setattr(npc_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")

    with pytest.raises(ValueError):
        NpcService().create_override("!!!")


def test_scene_service_create_override_creates_only_directory(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    target_dir = SceneService().create_override("park")

    assert target_dir.is_dir()
    assert not (target_dir / "scene.md").exists()
    assert not (target_dir / "img.png").exists()


def test_scene_service_create_override_is_idempotent_for_existing_directory(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    existing_dir = tmp_path / ".overrides" / "scenes" / "park"
    existing_dir.mkdir(parents=True)

    target_dir = SceneService().create_override("park")
    assert target_dir == existing_dir


def test_scene_service_create_override_normalizes_name_to_snake_case(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")

    target_dir = SceneService().create_override("City Walk 2026")
    assert target_dir.name == "city_walk_2026"


def test_scene_service_create_override_rejects_invalid_name(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")

    with pytest.raises(ValueError):
        SceneService().create_override("@@@")

