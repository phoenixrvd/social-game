from pathlib import Path

from typer.testing import CliRunner
import yaml

import engine.cli as cli_module
from engine.cli import app

runner = CliRunner()


def override_npc_service(monkeypatch, fake_service_class):
    monkeypatch.setattr(cli_module, "NpcService", fake_service_class)


def override_npc_scene_service(monkeypatch, fake_service_class):
    monkeypatch.setattr(cli_module, "NpcSceneService", fake_service_class)


def test_hello():
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "Hello from Social Game CLI" in result.output


def test_hallo_llm_command_removed():
    result = runner.invoke(app, ["hallo-llm"])
    assert result.exit_code != 0
    assert "No such command" in result.output


def test_warmup_embeddings_command_removed():
    result = runner.invoke(app, ["warmup-embeddings"])
    assert result.exit_code != 0
    assert "No such command" in result.output


def test_web_command_starts_web_gui(monkeypatch):
    captured: dict[str, object] = {}

    def run(*, host: str, port: int, reload: bool) -> None:
        captured["host"] = host
        captured["port"] = port
        captured["reload"] = reload

    monkeypatch.setattr("engine.web.app.run", run)

    result = runner.invoke(app, ["web", "--host", "0.0.0.0", "--port", "8123", "--reload"])

    assert result.exit_code == 0
    assert captured == {"host": "0.0.0.0", "port": 8123, "reload": True}


def test_web_command_reports_error(monkeypatch):
    def run(*, host: str, port: int, reload: bool) -> None:
        _ = host, port, reload
        raise RuntimeError("kaputt")

    monkeypatch.setattr("engine.web.app.run", run)

    result = runner.invoke(app, ["web"])

    assert result.exit_code == 1
    assert result.output == ""
    assert isinstance(result.exception, RuntimeError)
    assert "kaputt" in str(result.exception)


def test_root_help_uses_normal_descriptions():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Tools f\u00fcr Social Game." in result.output
    assert "Anforderungen" not in result.output
    assert "SG-002" not in result.output
    assert "SG-004" not in result.output
    assert "SG-005" not in result.output


def test_group_help_uses_normal_descriptions():
    checks = [
        (["npc-create", "--help"], "Legt einen neuen NPC unter .overrides/npcs/<npc_id>/ an."),
    ]

    for command, expected_text in checks:
        result = runner.invoke(app, command)
        assert result.exit_code == 0
        assert expected_text in result.output
        assert "SG-" not in result.output


def test_chat_command_is_no_longer_registered():
    result = runner.invoke(app, ["chat", "--help"])
    assert result.exit_code != 0
    assert "No such command" in result.output
    assert "chat" in result.output


def test_update_command_is_no_longer_registered():
    result = runner.invoke(app, ["update", "--help"])
    assert result.exit_code != 0
    assert "No such command" in result.output
    assert "update" in result.output


def test_watch_changes_command_removed():
    result = runner.invoke(app, ["watch", "changes"])

    assert result.exit_code != 0
    assert "No such command 'watch'" in result.output


def test_watch_refresh_command_removed():
    result = runner.invoke(app, ["watch", "refresh", "relationship"])

    assert result.exit_code != 0
    assert "No such command 'watch'" in result.output


def test_watch_image_revert_command_removed():
    result = runner.invoke(app, ["watch", "image-revert"])

    assert result.exit_code != 0
    assert "No such command 'watch'" in result.output


def test_update_command_call_is_rejected():
    result = runner.invoke(app, ["update", "scene"])
    assert result.exit_code != 0
    assert "No such command" in result.output


def test_update_option_debug_removed():
    result = runner.invoke(app, ["update", "scene", "--debug"])
    assert result.exit_code != 0
    assert "No such command" in result.output


def test_update_option_persist_removed():
    result = runner.invoke(app, ["update", "scene", "--persist"])
    assert result.exit_code != 0
    assert "No such command" in result.output


def test_scene_group_is_no_longer_registered():
    result = runner.invoke(app, ["scene", "--help"])
    assert result.exit_code != 0
    assert "No such command" in result.output
    assert "scene" in result.output


def test_state_group_is_no_longer_registered():
    result = runner.invoke(app, ["state", "--help"])
    assert result.exit_code != 0
    assert "No such command" in result.output
    assert "state" in result.output


def test_memory_group_is_no_longer_registered():
    result = runner.invoke(app, ["memory", "--help"])
    assert result.exit_code != 0
    assert "No such command" in result.output
    assert "memory" in result.output


def test_session_group_is_no_longer_registered():
    result = runner.invoke(app, ["session", "--help"])
    assert result.exit_code != 0
    assert "No such command" in result.output
    assert "session" in result.output


def test_session_set_command_removed():
    result = runner.invoke(app, ["session-set"])
    assert result.exit_code != 0
    assert "No such command" in result.output


def test_image_revert_command_removed():
    result = runner.invoke(app, ["image-revert"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_image_merge_scene_command_removed():
    result = runner.invoke(app, ["image-merge-scene"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_image_refresh_command_removed():
    result = runner.invoke(app, ["image-refresh"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_removed_top_level_aliases_fail():
    for command in (
        ["refresh", "relationship", "--npc", "vika"],
        ["refresh", "state", "--npc", "vika"],
        ["refresh", "image", "--npc", "vika"],
        ["dump-system-prompt", "--npc", "vika"],
    ):
        result = runner.invoke(app, command)
        assert result.exit_code != 0
        assert "No such command" in result.output




def test_npc_create_calls_npc_service(monkeypatch, tmp_path):
    calls: list[str] = []

    class FakeNpcService:
        def create_override(self, npc_id: str):
            calls.append(npc_id)
            return tmp_path / ".overrides" / "npcs" / npc_id

    override_npc_service(monkeypatch, FakeNpcService)

    result = runner.invoke(app, ["npc-create", " alex "])

    assert result.exit_code == 0
    assert calls == [" alex "]
    assert "NPC angelegt" in result.output


def test_npc_create_allows_existing_target_without_error(tmp_path, monkeypatch):
    monkeypatch.setattr(cli_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    target = tmp_path / ".overrides" / "npcs" / "alex"
    target.mkdir(parents=True)
    (target / "character.yaml").write_text("name: Bestehend\n", encoding="utf-8")

    result = runner.invoke(app, ["npc-create", "alex"])

    assert result.exit_code == 0
    assert (target / "character.yaml").read_text(encoding="utf-8") == "name: Bestehend\n"


def test_npc_create_creates_override_dataset_with_character_yaml(tmp_path, monkeypatch):
    monkeypatch.setattr(cli_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")

    result = runner.invoke(app, ["npc-create", "alex"])

    assert result.exit_code == 0
    target = tmp_path / ".overrides" / "npcs" / "alex"
    assert (target / "character.yaml").is_file()
    assert yaml.safe_load((target / "character.yaml").read_text(encoding="utf-8")) == {"name": "alex"}
    assert not (target / "description.md").exists()
    assert "id=alex" in result.output


def test_npc_create_normalizes_name_to_snake_case(tmp_path, monkeypatch):
    monkeypatch.setattr(cli_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")

    result = runner.invoke(app, ["npc-create", "Anna Maria!!!"])

    assert result.exit_code == 0
    target = tmp_path / ".overrides" / "npcs" / "anna_maria"
    assert (target / "character.yaml").is_file()
    assert "id=anna_maria" in result.output


def test_npc_create_rejects_invalid_normalized_name():
    result = runner.invoke(app, ["npc-create", "!!!"])

    assert result.exit_code == 1
    assert "NPC-Name ergibt keine gueltige ID." in result.output


def test_scene_create_command_removed():
    result = runner.invoke(app, ["scene-create", "Ruhiger Stadtpark mit See."])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_npc_scene_create_calls_npc_scene_service(monkeypatch, tmp_path):
    calls: list[str] = []

    class FakeNpcSceneService:
        def create_override(self, short_description: str):
            calls.append(short_description)
            return tmp_path / ".overrides" / "npcs" / "vika" / "scenes" / "cafe" / "scene.md"

    override_npc_scene_service(monkeypatch, FakeNpcSceneService)

    result = runner.invoke(app, ["npc-scene-create", "stimmungsvolle details fuer vika im cafe"])

    assert result.exit_code == 0
    assert calls == ["stimmungsvolle details fuer vika im cafe"]
    assert "NPC-Scene angelegt" in result.output


def test_npc_scene_create_rejects_blank_short_description():
    result = runner.invoke(app, ["npc-scene-create", "   "])

    assert result.exit_code == 1
    assert "Kurzbeschreibung darf nicht leer sein." in result.output


def test_icons_command_runs_pipeline(monkeypatch, tmp_path):
    icons_dir = tmp_path / "engine" / "web" / "static" / "icons"
    icons_dir.mkdir(parents=True)
    input_path = icons_dir / "origin.png"
    input_path.write_bytes(b"png")

    captured: dict[str, object] = {}
    saved_paths: list[tuple[Path, str | None, object]] = []
    resize_calls: list[tuple[object, object]] = []
    pasted: tuple[object, tuple[int, int], object] | None = None

    class FakeSource:
        width = 320
        height = 640

        def convert(self, mode):
            captured["convert_mode"] = mode
            return self

    class FakeBase:
        def paste(self, source, xy, mask):
            nonlocal pasted
            pasted = (source, xy, mask)
            captured["paste"] = (source, xy, mask)

        def save(self, path, format=None, sizes=None):
            saved_paths.append((Path(path), format, sizes))

        def resize(self, size, resample):
            resize_calls.append((size, resample))
            return self

    monkeypatch.setattr(cli_module.config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cli_module.Image, "open", lambda path: FakeSource())
    monkeypatch.setattr(cli_module.Image, "new", lambda mode, size, color: FakeBase())

    result = runner.invoke(app, ["icons", "--input", str(input_path)])

    assert result.exit_code == 0
    assert captured["convert_mode"] == "RGBA"
    assert pasted is not None
    assert pasted[1] == ((1024 - 320) // 2, (1024 - 640) // 2)
    assert saved_paths[0][0] == icons_dir / "base.png"
    assert resize_calls
    assert "Icons erfolgreich generiert." in result.output


def test_icons_command_requires_existing_input(monkeypatch, tmp_path):
    monkeypatch.setattr(cli_module.config, "PROJECT_ROOT", tmp_path)

    result = runner.invoke(app, ["icons", "--input", str(tmp_path / "missing.png")])

    assert result.exit_code == 1
    assert "Eingabebild nicht gefunden" in result.output


def test_icons_command_reports_generation_failure(monkeypatch, tmp_path):
    icons_dir = tmp_path / "engine" / "web" / "static" / "icons"
    icons_dir.mkdir(parents=True)
    input_path = icons_dir / "origin.png"
    input_path.write_bytes(b"png")

    def fake_open(_path):
        raise RuntimeError("kaputt")

    monkeypatch.setattr(cli_module.config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cli_module.Image, "open", fake_open)

    result = runner.invoke(app, ["icons", "--input", str(input_path)])

    assert result.exit_code == 1
    assert isinstance(result.exception, RuntimeError)
    assert "kaputt" in str(result.exception)
