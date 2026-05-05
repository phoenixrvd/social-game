import pytest
import yaml

from engine.config import config
from engine.services.id_normalizer import normalize_to_snake_id
from engine.services.npc_scene_service import NpcSceneService
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


def test_scene_service_create_override_creates_scene_markdown_and_image(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    captured: dict[str, object] = {}

    def fake_run_prompt_small_model(prompt: str, response_model: type[scene_module.SceneDraft]) -> scene_module.SceneDraft:
        captured["prompt"] = prompt
        captured["response_model"] = response_model
        return response_model(
            location_name="Abendlicher Stadtpark",
            scene_description="Ein ruhiger Park mit kleinem See und warmen Laternenlichtern.",
        )

    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(scene_module.client, "run_prompt_small_model", fake_run_prompt_small_model)
    monkeypatch.setattr(scene_module.client, "generate_scene_img", lambda _prompt: b"png-bytes")
    target_dir = SceneService().create_override("Ruhiger Stadtpark mit See.")

    assert target_dir.is_dir()
    assert "Ruhiger Stadtpark mit See." in captured["prompt"]
    assert captured["response_model"] is scene_module.SceneDraft
    assert (target_dir / "scene.md").read_text(encoding="utf-8") == (
        "## Abendlicher Stadtpark\n\n"
        "Ein ruhiger Park mit kleinem See und warmen Laternenlichtern.\n"
    )
    assert (target_dir / "img.png").read_bytes() == b"png-bytes"


def test_scene_service_create_override_suffixes_existing_directory(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    existing_dir = tmp_path / ".overrides" / "scenes" / "abendlicher_stadtpark"
    next_dir = tmp_path / ".overrides" / "scenes" / "abendlicher_stadtpark_1"
    existing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        scene_module.client,
        "run_prompt_small_model",
        lambda _prompt, response_model: response_model(
            location_name="Abendlicher Stadtpark",
            scene_description="Ein ruhiger Park mit kleinem See und warmen Laternenlichtern.",
        ),
    )
    monkeypatch.setattr(scene_module.client, "generate_scene_img", lambda _prompt: b"png-bytes")

    target_dir = SceneService().create_override("Ruhiger Stadtpark mit See.")
    assert target_dir == next_dir


def test_scene_service_create_override_increments_suffix_until_free(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    for suffix in ("abendlicher_stadtpark", "abendlicher_stadtpark_1"):
        (tmp_path / ".overrides" / "scenes" / suffix).mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        scene_module.client,
        "run_prompt_small_model",
        lambda _prompt, response_model: response_model(
            location_name="Abendlicher Stadtpark",
            scene_description="Ein ruhiger Park mit kleinem See und warmen Laternenlichtern.",
        ),
    )
    monkeypatch.setattr(scene_module.client, "generate_scene_img", lambda _prompt: b"png-bytes")

    target_dir = SceneService().create_override("Ruhiger Stadtpark mit See.")

    assert target_dir.name == "abendlicher_stadtpark_2"


def test_scene_service_create_override_normalizes_name_to_snake_case(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(
        scene_module.client,
        "run_prompt_small_model",
        lambda _prompt, response_model: response_model(
            location_name="Innenstadt",
            scene_description="Eine breite Strasse mit Schaufenstern.",
        ),
    )
    monkeypatch.setattr(scene_module.client, "generate_scene_img", lambda _prompt: b"png-bytes")

    target_dir = SceneService().create_override("Breite Strasse mit Schaufenstern.")
    assert target_dir.name == "innenstadt"


def test_scene_service_create_override_rejects_invalid_name(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(
        scene_module.client,
        "run_prompt_small_model",
        lambda _prompt, response_model: response_model(location_name="@@@", scene_description="Kurzbeschreibung"),
    )

    with pytest.raises(ValueError):
        SceneService().create_override("Kurzbeschreibung")


def test_scene_service_create_override_rejects_blank_short_description(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")

    with pytest.raises(ValueError):
        SceneService().create_override("   ")


def test_scene_service_create_override_rejects_invalid_llm_output(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(
        scene_module.client,
        "run_prompt_small_model",
        lambda _prompt, response_model: (_ for _ in ()).throw(RuntimeError("Scene-Erstellung lieferte ungueltige Felder.")),
    )

    with pytest.raises(RuntimeError):
        SceneService().create_override("Ruhiger Stadtpark mit See.")


def test_npc_scene_service_create_override_writes_active_npc_scene_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_PROMPTS_DIR", tmp_path / ".overrides" / "prompts")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")
    (tmp_path / "npcs" / "vika").mkdir(parents=True)
    (tmp_path / "npcs" / "vika" / "character.yaml").write_text("name: Vika\n", encoding="utf-8")
    (tmp_path / "npcs" / "vika" / "description.md").write_text("Vika ist ruhig und praezise.", encoding="utf-8")
    (tmp_path / "scenes" / "cafe").mkdir(parents=True)
    (tmp_path / "scenes" / "cafe" / "scene.md").write_text("Ein ruhiges Cafe am Abend.", encoding="utf-8")
    (tmp_path / "prompts").mkdir(parents=True)
    (tmp_path / "prompts" / "npc_scene_create_text.md").write_text(
        "{{SHORT_DESCRIPTION}}|{{NPC_DESCRIPTION}}|{{SCENE_DESCRIPTION}}",
        encoding="utf-8",
    )
    monkeypatch.setattr("engine.services.npc_scene_service.client.run_prompt_small", lambda prompt: f"## Titel\n\n{prompt[:120]}")

    target_file = NpcSceneService().create_override("Fensterplatz mit Notizbuch")

    assert target_file == tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / "cafe" / "scene.md"
    saved = target_file.read_text(encoding="utf-8")
    assert saved.startswith("## Titel\n\nFensterplatz mit Notizbuch|Vika ist ruhig und praezise.|Ein ruhiges Cafe am Abend.")


def test_npc_scene_service_create_override_rejects_blank_llm_result(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_PROMPTS_DIR", tmp_path / ".overrides" / "prompts")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")

    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: cafe\n", encoding="utf-8")
    (tmp_path / "npcs" / "vika").mkdir(parents=True)
    (tmp_path / "scenes" / "cafe").mkdir(parents=True)
    (tmp_path / "prompts").mkdir(parents=True)
    (tmp_path / "prompts" / "npc_scene_create_text.md").write_text("{{SHORT_DESCRIPTION}}", encoding="utf-8")
    monkeypatch.setattr("engine.services.npc_scene_service.client.run_prompt_small", lambda _prompt: "   ")

    with pytest.raises(RuntimeError):
        NpcSceneService().create_override("Kurz")


def test_npc_service_reset_active_runtime_deletes_active_scene_runtime(tmp_path, monkeypatch):
    import engine.services.npc_service as npc_module

    monkeypatch.setattr(config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "OVERRIDES_PROMPTS_DIR", tmp_path / ".overrides" / "prompts")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / ".data" / "npcs")

    (tmp_path / "session.yaml").write_text("npc_id: vika\nscene_id: office\n", encoding="utf-8")
    (tmp_path / "npcs" / "vika").mkdir(parents=True)
    (tmp_path / "npcs" / "vika" / "character.yaml").write_text("name: Vika\n", encoding="utf-8")
    (tmp_path / "scenes" / "office").mkdir(parents=True)
    (tmp_path / "scenes" / "office" / "scene.md").write_text("# Office\n", encoding="utf-8")
    runtime_dir = tmp_path / ".data" / "npcs" / "vika" / "office"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "stm.jsonl").write_text("{}\n", encoding="utf-8")

    npc_module.NpcService.reset_active_runtime()

    assert not runtime_dir.exists()


def test_scene_service_dynamic_scene_detection_and_cleanup(tmp_path, monkeypatch):
    import engine.services.scene_service as scene_module

    monkeypatch.setattr(scene_module.config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(scene_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(scene_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    scene_id = "created_alley"
    dynamic_scene_dir = tmp_path / ".overrides" / "scenes" / scene_id
    dynamic_scene_dir.mkdir(parents=True)
    (dynamic_scene_dir / "scene.md").write_text("# Alley\n", encoding="utf-8")

    vika_override = tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / scene_id
    mira_override = tmp_path / ".overrides" / "npcs" / "mira" / "scenes" / scene_id
    vika_override.mkdir(parents=True, exist_ok=True)
    mira_override.mkdir(parents=True, exist_ok=True)
    (vika_override / "scene.md").write_text("vika\n", encoding="utf-8")
    (mira_override / "scene.md").write_text("mira\n", encoding="utf-8")

    scene_module.SceneService.delete_dynamic_scene_artifacts(scene_id)

    assert not dynamic_scene_dir.exists()
    assert not vika_override.exists()
    assert not mira_override.exists()


