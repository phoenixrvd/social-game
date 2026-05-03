from __future__ import annotations

import importlib
import dotenv

import engine.config as config_module


def test_config_uses_int_env_overrides(monkeypatch):
    monkeypatch.setenv("SG_MODEL_API_KEY", "test-openai-key")
    monkeypatch.setenv("SG_DEFAULT_NPC_ID", "mira")
    monkeypatch.setenv("SG_DEFAULT_SCENE_ID", "cafe")
    monkeypatch.setenv("SG_UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP", "25")
    monkeypatch.setenv("SG_UPDATER_ETM_BATCH_SIZE_THRESHOLD", "9")
    monkeypatch.setenv("SG_ETM_RETRIEVAL_TOP_K", "6")
    monkeypatch.setenv("SG_ETM_RETRIEVAL_MAX_DISTANCE", "0.25")
    monkeypatch.setenv("SG_STM_LATEST_MESSAGES", "8")
    monkeypatch.setenv("SG_UPDATER_ETM_CHECK_INTERVAL_SECONDS", "500")
    monkeypatch.setenv("SG_UPDATER_SCENE_CHECK_INTERVAL_SECONDS", "45")
    monkeypatch.setenv("SG_UPDATER_STATE_CHECK_INTERVAL_SECONDS", "55")
    monkeypatch.setenv("SG_UPDATER_IMAGE_CHECK_INTERVAL_SECONDS", "70")

    cfg = importlib.reload(config_module)

    assert cfg.config.DEFAULT_NPC_ID == "mira"
    assert cfg.config.DEFAULT_SCENE_ID == "cafe"
    assert cfg.config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP == 25
    assert cfg.config.UPDATER_ETM_BATCH_SIZE_THRESHOLD == 9
    assert cfg.config.ETM_RETRIEVAL_TOP_K == 6
    assert cfg.config.ETM_RETRIEVAL_MAX_DISTANCE == 0.25
    assert cfg.config.STM_LATEST_MESSAGES == 8
    assert cfg.config.UPDATER_ETM_CHECK_INTERVAL_SECONDS == 500
    assert cfg.config.UPDATER_SCENE_CHECK_INTERVAL_SECONDS == 45
    assert cfg.config.UPDATER_STATE_CHECK_INTERVAL_SECONDS == 55
    assert cfg.config.UPDATER_IMAGE_CHECK_INTERVAL_SECONDS == 70


def test_config_uses_defaults_when_env_missing(monkeypatch):
    monkeypatch.setenv("SG_MODEL_API_KEY", "test-openai-key")
    monkeypatch.delenv("SG_DEFAULT_NPC_ID", raising=False)
    monkeypatch.delenv("SG_DEFAULT_SCENE_ID", raising=False)
    monkeypatch.delenv("SG_UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP", raising=False)
    monkeypatch.delenv("SG_UPDATER_ETM_BATCH_SIZE_THRESHOLD", raising=False)
    monkeypatch.delenv("SG_ETM_RETRIEVAL_TOP_K", raising=False)
    monkeypatch.delenv("SG_ETM_RETRIEVAL_MAX_DISTANCE", raising=False)
    monkeypatch.delenv("SG_STM_LATEST_MESSAGES", raising=False)
    monkeypatch.delenv("SG_UPDATER_ETM_CHECK_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("SG_UPDATER_SCENE_CHECK_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("SG_UPDATER_STATE_CHECK_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("SG_UPDATER_IMAGE_CHECK_INTERVAL_SECONDS", raising=False)

    cfg = importlib.reload(config_module)

    assert cfg.config.DEFAULT_NPC_ID == "vika"
    assert cfg.config.DEFAULT_SCENE_ID == "office"
    assert cfg.config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP == 20
    assert cfg.config.UPDATER_ETM_BATCH_SIZE_THRESHOLD == 7
    assert cfg.config.ETM_RETRIEVAL_TOP_K == 4
    assert cfg.config.ETM_RETRIEVAL_MAX_DISTANCE == 0.75
    assert cfg.config.STM_LATEST_MESSAGES == 5
    assert cfg.config.UPDATER_ETM_CHECK_INTERVAL_SECONDS == 350
    assert cfg.config.UPDATER_SCENE_CHECK_INTERVAL_SECONDS == 30
    assert cfg.config.UPDATER_STATE_CHECK_INTERVAL_SECONDS == 30
    assert cfg.config.UPDATER_IMAGE_CHECK_INTERVAL_SECONDS == 60


def test_config_allows_empty_openai_key(monkeypatch):
    monkeypatch.setenv("SG_MODEL_API_KEY", "")

    cfg = importlib.reload(config_module)

    assert cfg.config.MODEL_API_KEY == ""


def test_config_uses_model_overrides(monkeypatch):
    monkeypatch.setenv("SG_MODEL_API_KEY", "test-openai-key")
    monkeypatch.setenv("SG_MODEL_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("SG_MODEL_LLM_BIG", "my-big-model")
    monkeypatch.setenv("SG_MODEL_LLM_SMALL", "my-small-model")
    monkeypatch.setenv("SG_MODEL_IMAGE", "my-image-model")
    monkeypatch.setenv("SG_MODEL_EMBEDDING", "my-embedding-model")

    cfg = importlib.reload(config_module)

    assert cfg.config.MODEL_LLM_BIG == "my-big-model"
    assert cfg.config.MODEL_LLM_SMALL == "my-small-model"
    assert cfg.config.MODEL_IMAGE == "my-image-model"
    assert cfg.config.MODEL_EMBEDDING == "my-embedding-model"
    assert cfg.config.MODEL_BASE_URL == "https://example.com/v1"


def test_config_uses_default_embeddings_model(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setenv("SG_MODEL_API_KEY", "test-openai-key")
    monkeypatch.delenv("SG_MODEL_EMBEDDING", raising=False)

    cfg = importlib.reload(config_module)

    assert cfg.config.MODEL_EMBEDDING == "text-embedding-3-small"

