from typing import cast

from apscheduler.schedulers.background import BackgroundScheduler
from typer.testing import CliRunner

import engine.cli as cli_module
import engine.updater.schedule as schedule_module
from engine.cli import app
from engine.models import Session

runner = CliRunner()


def test_hello():
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "Hello from Social Game CLI" in result.output


def test_hallo_llm(monkeypatch):
    monkeypatch.setattr(cli_module, "hello_llm", lambda: "pong")
    result = runner.invoke(app, ["hallo-llm"])
    assert result.exit_code == 0
    assert "pong" in result.output


def test_web_command_starts_web_gui(monkeypatch):
    captured: dict[str, object] = {}

    def fake_run_web(*, host: str, port: int, reload: bool) -> None:
        captured["host"] = host
        captured["port"] = port
        captured["reload"] = reload

    monkeypatch.setattr(cli_module, "_run_web", fake_run_web)

    result = runner.invoke(app, ["web", "--host", "0.0.0.0", "--port", "8123", "--reload"])

    assert result.exit_code == 0
    assert captured == {"host": "0.0.0.0", "port": 8123, "reload": True}


def test_web_command_reports_error(monkeypatch):
    def fake_run_web(*, host: str, port: int, reload: bool) -> None:
        _ = host, port, reload
        raise RuntimeError("kaputt")

    monkeypatch.setattr(cli_module, "_run_web", fake_run_web)

    result = runner.invoke(app, ["web"])

    assert result.exit_code == 1
    assert "Web-GUI konnte nicht gestartet werden" in result.output


def test_root_help_uses_normal_descriptions():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Werkzeuge fuer Web-GUI, Session, Updater und LLM-Pruefung im Social Game." in result.output
    assert "Anforderungen" not in result.output
    assert "SG-002" not in result.output
    assert "SG-004" not in result.output
    assert "SG-005" not in result.output


def test_group_help_uses_normal_descriptions():
    checks = [
        (["session", "--help"], "Globalen Session-Kontext fuer NPC und Szene setzen."),
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


def test_update_help_uses_user_facing_text():
    checks = [
        (["update", "--help"], "Fuehrt den gewaehlten Updater einmal ueber `schedule()` aus."),
    ]

    for command, expected_text in checks:
        result = runner.invoke(app, command)
        assert result.exit_code == 0
        assert expected_text in result.output
        assert "SG-" not in result.output


def test_start_scheduler_uses_dedicated_scheduler_intervals(monkeypatch):
    class FakeLtmUpdater:
        schedule_calls = 0

        def get_update_interval(self):
            return 350

        def schedule(self):
            type(self).schedule_calls += 1

    class FakeSceneUpdater:
        schedule_calls = 0

        def get_update_interval(self):
            return 60

        def schedule(self):
            type(self).schedule_calls += 1

    class FakeStateUpdater:
        schedule_calls = 0

        def get_update_interval(self):
            return 30

        def schedule(self):
            type(self).schedule_calls += 1

    class FakeImageUpdater:
        schedule_calls = 0

        def get_update_interval(self):
            return 45

        def schedule(self):
            type(self).schedule_calls += 1

    class FakeScheduler:
        def __init__(self):
            self.jobs = []
            self.started = False
            self.shutdown_called = False

        def add_job(self, func, trigger, **kwargs):
            self.jobs.append((func, trigger, kwargs))

        def start(self):
            self.started = True

        def shutdown(self, wait=False):
            self.shutdown_called = True

    fake_scheduler = FakeScheduler()

    monkeypatch.setattr(
        schedule_module,
        "UPDATER_CLASSES",
        (
            ("ltm", FakeLtmUpdater),
            ("scene", FakeSceneUpdater),
            ("state", FakeStateUpdater),
            ("image", FakeImageUpdater),
        ),
    )
    monkeypatch.setattr(schedule_module, "BackgroundScheduler", lambda: fake_scheduler)

    scheduler, _updaters = schedule_module.start_scheduler(run_immediately=True)

    assert scheduler is fake_scheduler
    assert FakeLtmUpdater.schedule_calls == 1
    assert FakeSceneUpdater.schedule_calls == 1
    assert FakeStateUpdater.schedule_calls == 1
    assert FakeImageUpdater.schedule_calls == 1
    assert fake_scheduler.started is True
    assert len(fake_scheduler.jobs) == 4

    ltm_job = fake_scheduler.jobs[0]
    assert ltm_job[1] == "interval"
    assert ltm_job[2]["seconds"] == 350

    scene_job = fake_scheduler.jobs[1]
    assert scene_job[1] == "interval"
    assert scene_job[2]["seconds"] == 60

    state_job = fake_scheduler.jobs[2]
    assert state_job[1] == "interval"
    assert state_job[2]["seconds"] == 30

    image_job = fake_scheduler.jobs[3]
    assert image_job[1] == "interval"
    assert image_job[2]["seconds"] == 45

    schedule_module.stop_scheduler(cast(BackgroundScheduler, cast(object, fake_scheduler)))
    assert fake_scheduler.shutdown_called is True


def test_watch_changes_command_removed():
    result = runner.invoke(app, ["watch", "changes"])

    assert result.exit_code != 0
    assert "No such command 'watch'" in result.output


def test_watch_refresh_command_removed():
    result = runner.invoke(app, ["watch", "refresh", "ltm"])

    assert result.exit_code != 0
    assert "No such command 'watch'" in result.output


def test_watch_image_revert_command_removed():
    result = runner.invoke(app, ["watch", "image-revert"])

    assert result.exit_code != 0
    assert "No such command 'watch'" in result.output


def test_update_calls_schedule(monkeypatch):
    class FakeUpdater:
        def __init__(self):
            self.schedule_calls = 0

        def schedule(self):
            self.schedule_calls += 1

    fake_updater = FakeUpdater()
    monkeypatch.setattr(cli_module, "resolve_updater", lambda _name: fake_updater)

    result = runner.invoke(app, ["update", "scene"])
    assert result.exit_code == 0
    assert fake_updater.schedule_calls == 1


def test_update_unknown_updater():
    result = runner.invoke(app, ["update", "unknown-updater"])
    assert result.exit_code != 0
    assert "Unbekannter Updater" in result.output


def test_resolve_updater_uses_current_updater_classes(monkeypatch):
    class FakeDynamicUpdater:
        pass

    monkeypatch.setattr(cli_module, "UPDATER_CLASSES", (("dynamic", FakeDynamicUpdater),))

    resolved = cli_module.resolve_updater("dynamic")

    assert isinstance(resolved, FakeDynamicUpdater)


def test_update_option_debug_removed():
    result = runner.invoke(app, ["update", "scene", "--debug"])
    assert result.exit_code != 0
    assert "No such option: --debug" in result.output


def test_update_option_persist_removed():
    result = runner.invoke(app, ["update", "scene", "--persist"])
    assert result.exit_code != 0
    assert "No such option: --persist" in result.output


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


def test_revert_image_nothing_to_revert(monkeypatch):
    class FakeImageUpdater:
        def revert(self):
            return "Kein Daten-Bild vorhanden fuer 'vika'.", False

    monkeypatch.setattr(cli_module, "ImageUpdater", FakeImageUpdater)

    result = runner.invoke(app, ["image-revert"])
    assert result.exit_code == 0
    assert "Kein Daten-Bild vorhanden" in result.output
    assert "Abgeschlossen" not in result.output


def test_revert_image_deleted_and_restored(monkeypatch):
    class FakeImageUpdater:
        def revert(self):
            return "Bild geloescht.\nBackup wiederhergestellt: /tmp/character_backup/character-20260315-093000.png -> /tmp/character.png", True

    monkeypatch.setattr(cli_module, "ImageUpdater", FakeImageUpdater)

    result = runner.invoke(app, ["image-revert"])
    assert result.exit_code == 0
    assert "Bild geloescht." in result.output
    assert "Backup wiederhergestellt" in result.output
    assert "[image revert] Abgeschlossen." in result.output


def test_revert_image_not_available(monkeypatch):
    class FakeImageUpdater:
        pass

    monkeypatch.setattr(cli_module, "ImageUpdater", FakeImageUpdater)

    result = runner.invoke(app, ["image-revert"])
    assert result.exit_code == 1
    assert result.output == ""
    assert isinstance(result.exception, AttributeError)
    assert "revert" in str(result.exception)


def test_removed_top_level_aliases_fail():
    for command in (
        ["refresh", "ltm", "--npc", "vika"],
        ["refresh", "state", "--npc", "vika"],
        ["refresh", "image", "--npc", "vika"],
        ["dump-system-prompt", "--npc", "vika"],
    ):
        result = runner.invoke(app, command)
        assert result.exit_code != 0
        assert "No such command" in result.output


def test_session_set_saves_context(monkeypatch):
    class FakeSessionStore:
        def save(self, *, npc=None, scene=None):
            assert npc == "vika"
            assert scene == "default"
            return Session(npc_id=npc, scene_id=scene)

    monkeypatch.setattr(cli_module, "SessionStore", FakeSessionStore)

    result = runner.invoke(app, ["session", "set", "--npc", "vika", "--scene", "default"])
    assert result.exit_code == 0
    assert "Session-Kontext gespeichert." in result.output
    assert "npc=vika" in result.output
    assert "scene=default" in result.output


def test_session_set_requires_value():
    result = runner.invoke(app, ["session", "set"])
    assert result.exit_code == 1
    assert "Mindestens --npc oder --scene muss angegeben werden." in result.output


def test_icons_command_runs_pipeline(monkeypatch, tmp_path):
    icons_dir = tmp_path / "engine" / "web" / "static" / "icons"
    icons_dir.mkdir(parents=True)
    input_path = icons_dir / "origin.png"
    input_path.write_bytes(b"png")

    captured: dict[str, object] = {}

    def fake_generate_icons(*, input_path, output_dir):
        captured["input_path"] = input_path
        captured["output_dir"] = output_dir

    monkeypatch.setattr(cli_module.config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cli_module, "_generate_icons", fake_generate_icons)

    result = runner.invoke(app, ["icons", "--input", str(input_path)])

    assert result.exit_code == 0
    assert captured["input_path"] == input_path
    assert captured["output_dir"] == icons_dir
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

    def fake_generate_icons(*, input_path, output_dir):
        _ = input_path, output_dir
        raise RuntimeError("kaputt")

    monkeypatch.setattr(cli_module.config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cli_module, "_generate_icons", fake_generate_icons)

    result = runner.invoke(app, ["icons", "--input", str(input_path)])

    assert result.exit_code == 1
    if result.exception is not None:
        assert isinstance(result.exception, RuntimeError)
        assert "kaputt" in str(result.exception)
    else:
        assert "Icon-Generierung fehlgeschlagen" in result.output


