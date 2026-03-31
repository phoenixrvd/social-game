from __future__ import annotations

import importlib

import engine.config as config_module


def test_config_uses_int_env_overrides(monkeypatch):
    monkeypatch.setenv("UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP", "25")
    monkeypatch.setenv("UPDATER_LTM_BATCH_SIZE_THRESHOLD", "9")
    monkeypatch.setenv("STATE_AUTO_TRIGGER_LAST_N_MESSAGES", "8")
    monkeypatch.setenv("UPDATER_LTM_CHECK_INTERVAL_SECONDS", "500")
    monkeypatch.setenv("UPDATER_SCENE_CHECK_INTERVAL_SECONDS", "45")
    monkeypatch.setenv("UPDATER_STATE_CHECK_INTERVAL_SECONDS", "55")
    monkeypatch.setenv("UPDATER_IMAGE_CHECK_INTERVAL_SECONDS", "70")
    monkeypatch.setenv("APP_LOG_MAX_SIZE_MB", "3")
    monkeypatch.setenv("APP_LOG_BACKUP_COUNT", "11")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_SHOW_IN_CLI", "0")

    cfg = importlib.reload(config_module)

    assert cfg.config.UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP == 25
    assert cfg.config.UPDATER_LTM_BATCH_SIZE_THRESHOLD == 9
    assert cfg.config.STATE_AUTO_TRIGGER_LAST_N_MESSAGES == 8
    assert cfg.config.UPDATER_LTM_CHECK_INTERVAL_SECONDS == 500
    assert cfg.config.UPDATER_SCENE_CHECK_INTERVAL_SECONDS == 45
    assert cfg.config.UPDATER_STATE_CHECK_INTERVAL_SECONDS == 55
    assert cfg.config.UPDATER_IMAGE_CHECK_INTERVAL_SECONDS == 70
    assert cfg.config.APP_LOG_MAX_SIZE_MB == 3
    assert cfg.config.APP_LOG_BACKUP_COUNT == 11
    assert cfg.config.LOG_LEVEL == "DEBUG"
    assert cfg.config.LOG_SHOW_IN_CLI is False


def test_config_uses_defaults_when_env_missing(monkeypatch):
    monkeypatch.delenv("UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP", raising=False)
    monkeypatch.delenv("UPDATER_LTM_BATCH_SIZE_THRESHOLD", raising=False)
    monkeypatch.delenv("STATE_AUTO_TRIGGER_LAST_N_MESSAGES", raising=False)
    monkeypatch.delenv("UPDATER_LTM_CHECK_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("UPDATER_SCENE_CHECK_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("UPDATER_STATE_CHECK_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("UPDATER_IMAGE_CHECK_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("APP_LOG_MAX_SIZE_MB", raising=False)
    monkeypatch.delenv("APP_LOG_BACKUP_COUNT", raising=False)
    # LOG_* kann lokal aus .env kommen; für einen stabilen Default-Test hier explizit setzen.
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_SHOW_IN_CLI", "1")

    cfg = importlib.reload(config_module)

    assert cfg.config.UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP == 20
    assert cfg.config.UPDATER_LTM_BATCH_SIZE_THRESHOLD == 7
    assert cfg.config.STATE_AUTO_TRIGGER_LAST_N_MESSAGES == 5
    assert cfg.config.UPDATER_LTM_CHECK_INTERVAL_SECONDS == 350
    assert cfg.config.UPDATER_SCENE_CHECK_INTERVAL_SECONDS == 30
    assert cfg.config.UPDATER_STATE_CHECK_INTERVAL_SECONDS == 30
    assert cfg.config.UPDATER_IMAGE_CHECK_INTERVAL_SECONDS == 60
    assert cfg.config.APP_LOG_MAX_SIZE_MB == 1
    assert cfg.config.APP_LOG_BACKUP_COUNT == 2
    assert cfg.config.LOG_LEVEL == "INFO"
    assert cfg.config.LOG_SHOW_IN_CLI is True

