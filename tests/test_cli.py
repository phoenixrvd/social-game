from pathlib import Path

from typer.testing import CliRunner

import engine.cli as cli_module
from engine.cli import app

runner = CliRunner()


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


def test_etm_ui_starts_lightrag_server_for_active_context(monkeypatch, tmp_path):
    etm_dir = tmp_path / "etm_lightrag"
    captured: dict[str, object] = {}

    class FakeSession:
        npc_id = "ben"
        scene_id = "office"

    class FakeStorage:
        session = FakeSession()
        npc = type("FakeNpc", (), {"etm_dir": etm_dir})()

    def fake_run(command, check, env):
        captured["command"] = command
        captured["check"] = check
        captured["env"] = env

    monkeypatch.setattr(cli_module, "storage", FakeStorage())
    monkeypatch.setattr(cli_module.config, "MODEL_BASE_URL", "https://models.example/v1")
    monkeypatch.setattr(cli_module.config, "MODEL_API_KEY", "test-key")
    monkeypatch.setattr(cli_module.config, "MODEL_LLM_SMALL", "small-model")
    monkeypatch.setattr(cli_module.config, "MODEL_EMBEDDING", "embedding-model")
    monkeypatch.setattr(cli_module.config, "MODEL_EMBEDDING_DIMENSIONS", 42)
    monkeypatch.setattr(cli_module.subprocess, "run", fake_run)

    result = runner.invoke(app, ["etm-ui", "--host", "0.0.0.0", "--port", "9721"])

    assert result.exit_code == 0
    assert captured["command"] == ["lightrag-server"]
    assert captured["check"] is True
    env = captured["env"]
    assert env["WORKING_DIR"] == str(etm_dir)
    assert env["HOST"] == "0.0.0.0"
    assert env["PORT"] == "9721"
    assert env["LLM_BINDING"] == "openai"
    assert env["EMBEDDING_BINDING"] == "openai"
    assert env["LLM_BINDING_HOST"] == "https://models.example/v1"
    assert env["LLM_MODEL"] == "small-model"
    assert env["EMBEDDING_MODEL"] == "embedding-model"
    assert env["EMBEDDING_DIM"] == "42"
    assert etm_dir.is_dir()
    assert "ETM-UI: http://0.0.0.0:9721" in result.output


def test_etm_ui_watch_mode_uses_watch_runner(monkeypatch, tmp_path):
    etm_dir = tmp_path / "etm_lightrag"
    captured: dict[str, object] = {}

    class FakeSession:
        npc_id = "ben"
        scene_id = "office"

    class FakeStorage:
        session = FakeSession()
        npc = type("FakeNpc", (), {"etm_dir": etm_dir})()

    def fake_watch(host: str, port: int, interval_seconds: float) -> None:
        captured["host"] = host
        captured["port"] = port
        captured["interval_seconds"] = interval_seconds

    def fake_run(*_args, **_kwargs) -> None:
        raise AssertionError("subprocess.run must not be used in watch mode")

    monkeypatch.setattr(cli_module, "storage", FakeStorage())
    monkeypatch.setattr(cli_module, "_run_etm_ui_watch", fake_watch)
    monkeypatch.setattr(cli_module.subprocess, "run", fake_run)

    result = runner.invoke(app, ["etm-ui", "--watch", "--watch-interval", "1.5", "--host", "0.0.0.0", "--port", "9721"])

    assert result.exit_code == 0
    assert captured == {"host": "0.0.0.0", "port": 9721, "interval_seconds": 1.5}


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
        (["web", "--help"], "Startet die browserbasierte GUI."),
        (["etm-ui", "--help"], "Startet die LightRAG-WebUI"),
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


def test_npc_create_command_removed():
    result = runner.invoke(app, ["npc-create", "Alex, 28, arbeitet als Koch."])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_scene_create_command_removed():
    result = runner.invoke(app, ["scene-create", "Ruhiger Stadtpark mit See."])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_npc_scene_create_command_removed():
    result = runner.invoke(app, ["npc-scene-create", "stimmungsvolle details fuer vika im cafe"])

    assert result.exit_code != 0
    assert "No such command" in result.output


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


def test_npc_videos_strip_audio_processes_default_and_override_videos(monkeypatch, tmp_path):
    default_video = tmp_path / "npcs" / "vika" / "video.mp4"
    override_video = tmp_path / ".overrides" / "npcs" / "blacky" / "video.mp4"
    default_video.parent.mkdir(parents=True)
    override_video.parent.mkdir(parents=True)
    default_video.write_bytes(b"default")
    override_video.write_bytes(b"override")

    processed: list[Path] = []

    monkeypatch.setattr(cli_module.config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cli_module.config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(cli_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(cli_module, "_remove_audio_track", lambda path: processed.append(path))

    result = runner.invoke(app, ["npc-videos-strip-audio"])

    assert result.exit_code == 0
    assert processed == [override_video, default_video]
    assert "Audiospuren aus 2 NPC-Video(s) entfernt." in result.output


def test_npc_videos_strip_audio_processes_default_and_override_for_same_npc(monkeypatch, tmp_path):
    default_video = tmp_path / "npcs" / "olga" / "video.mp4"
    override_video = tmp_path / ".overrides" / "npcs" / "olga" / "video.mp4"
    default_video.parent.mkdir(parents=True)
    override_video.parent.mkdir(parents=True)
    default_video.write_bytes(b"default")
    override_video.write_bytes(b"override")

    processed: list[Path] = []

    monkeypatch.setattr(cli_module.config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cli_module.config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(cli_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(cli_module, "_remove_audio_track", lambda path: processed.append(path))

    result = runner.invoke(app, ["npc-videos-strip-audio"])

    assert result.exit_code == 0
    assert processed == [override_video, default_video]
    assert "Audiospuren aus 2 NPC-Video(s) entfernt." in result.output


def test_npc_videos_strip_audio_reports_missing_ffmpeg(monkeypatch, tmp_path):
    video_path = tmp_path / "npcs" / "vika" / "video.mp4"
    video_path.parent.mkdir(parents=True)
    video_path.write_bytes(b"video")

    def fail_remove_audio(_path):
        raise FileNotFoundError("ffmpeg")

    monkeypatch.setattr(cli_module.config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cli_module.config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(cli_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(cli_module, "_remove_audio_track", fail_remove_audio)

    result = runner.invoke(app, ["npc-videos-strip-audio"])

    assert result.exit_code == 1
    assert "ffmpeg nicht gefunden" in result.output


def test_remove_audio_track_uses_ffmpeg_and_replaces_video(monkeypatch, tmp_path):
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"with-audio")
    commands: list[list[str]] = []

    def fake_run(command, check):
        commands.append(command)
        Path(command[-1]).write_bytes(b"without-audio")
        assert check is True

    monkeypatch.setattr(cli_module.subprocess, "run", fake_run)

    cli_module._remove_audio_track(video_path)

    assert video_path.read_bytes() == b"without-audio"
    assert commands[0][:7] == ["ffmpeg", "-y", "-i", str(video_path), "-an", "-c:v", "copy"]
