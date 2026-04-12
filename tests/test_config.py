from __future__ import annotations

import importlib

import engine.config as config_module


def test_config_uses_int_env_overrides(monkeypatch):
    monkeypatch.setenv("UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP", "25")
    monkeypatch.setenv("UPDATER_ETM_BATCH_SIZE_THRESHOLD", "9")
    monkeypatch.setenv("ETM_RETRIEVAL_TOP_K", "6")
    monkeypatch.setenv("ETM_RETRIEVAL_MAX_DISTANCE", "0.25")
    monkeypatch.setenv("STATE_AUTO_TRIGGER_LAST_N_MESSAGES", "8")
    monkeypatch.setenv("UPDATER_ETM_CHECK_INTERVAL_SECONDS", "500")
    monkeypatch.setenv("UPDATER_SCENE_CHECK_INTERVAL_SECONDS", "45")
    monkeypatch.setenv("UPDATER_STATE_CHECK_INTERVAL_SECONDS", "55")
    monkeypatch.setenv("UPDATER_IMAGE_CHECK_INTERVAL_SECONDS", "70")

    cfg = importlib.reload(config_module)

    assert cfg.config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP == 25
    assert cfg.config.UPDATER_ETM_BATCH_SIZE_THRESHOLD == 9
    assert cfg.config.ETM_RETRIEVAL_TOP_K == 6
    assert cfg.config.ETM_RETRIEVAL_MAX_DISTANCE == 0.25
    assert cfg.config.STATE_AUTO_TRIGGER_LAST_N_MESSAGES == 8
    assert cfg.config.UPDATER_ETM_CHECK_INTERVAL_SECONDS == 500
    assert cfg.config.UPDATER_SCENE_CHECK_INTERVAL_SECONDS == 45
    assert cfg.config.UPDATER_STATE_CHECK_INTERVAL_SECONDS == 55
    assert cfg.config.UPDATER_IMAGE_CHECK_INTERVAL_SECONDS == 70


def test_config_uses_defaults_when_env_missing(monkeypatch):
    monkeypatch.delenv("UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP", raising=False)
    monkeypatch.delenv("UPDATER_ETM_BATCH_SIZE_THRESHOLD", raising=False)
    monkeypatch.delenv("ETM_RETRIEVAL_TOP_K", raising=False)
    monkeypatch.delenv("ETM_RETRIEVAL_MAX_DISTANCE", raising=False)
    monkeypatch.delenv("STATE_AUTO_TRIGGER_LAST_N_MESSAGES", raising=False)
    monkeypatch.delenv("UPDATER_ETM_CHECK_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("UPDATER_SCENE_CHECK_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("UPDATER_STATE_CHECK_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("UPDATER_IMAGE_CHECK_INTERVAL_SECONDS", raising=False)

    cfg = importlib.reload(config_module)

    assert cfg.config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP == 20
    assert cfg.config.UPDATER_ETM_BATCH_SIZE_THRESHOLD == 7
    assert cfg.config.ETM_RETRIEVAL_TOP_K == 4
    assert cfg.config.ETM_RETRIEVAL_MAX_DISTANCE == 0.75
    assert cfg.config.STATE_AUTO_TRIGGER_LAST_N_MESSAGES == 5
    assert cfg.config.UPDATER_ETM_CHECK_INTERVAL_SECONDS == 350
    assert cfg.config.UPDATER_SCENE_CHECK_INTERVAL_SECONDS == 30
    assert cfg.config.UPDATER_STATE_CHECK_INTERVAL_SECONDS == 30
    assert cfg.config.UPDATER_IMAGE_CHECK_INTERVAL_SECONDS == 60
