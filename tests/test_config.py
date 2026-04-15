from __future__ import annotations

import importlib

import engine.config as config_module


def test_config_uses_int_env_overrides(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
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
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
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


def test_config_uses_grok_switches_with_own_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GROK_API_KEY", "test-grok-key")
    monkeypatch.setenv("LLM_BIG", "grok")
    monkeypatch.setenv("LLM_SMALL", "grok")
    monkeypatch.setenv("IMAGE", "grok")

    cfg = importlib.reload(config_module)

    assert cfg.config.GROK_API_KEY == "test-grok-key"
    assert cfg.config.OPENAI_API_KEY == "test-openai-key"
    assert cfg.config.GROK_BASE_URL == "https://api.x.ai/v1"
    assert cfg.config.LLM_BIG == "grok"
    assert cfg.config.LLM_SMALL == "grok"
    assert cfg.config.IMAGE == "grok"


def test_config_allows_empty_provider_keys(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GROK_API_KEY", "")

    cfg = importlib.reload(config_module)

    assert cfg.config.OPENAI_API_KEY == ""
    assert cfg.config.GROK_API_KEY == ""


def test_config_uses_mixed_provider_switches(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GROK_API_KEY", "test-grok-key")
    monkeypatch.setenv("LLM_BIG", "grok")
    monkeypatch.setenv("LLM_SMALL", "openai")
    monkeypatch.setenv("IMAGE", "grok")
    monkeypatch.setenv("EMBEDDING", "openai")

    cfg = importlib.reload(config_module)

    assert cfg.config.LLM_BIG == "grok"
    assert cfg.config.LLM_SMALL == "openai"
    assert cfg.config.IMAGE == "grok"
    assert cfg.config.EMBEDDING == "openai"


def test_config_allows_local_grok_embedding_without_grok_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GROK_API_KEY", "")
    monkeypatch.setenv("LLM_BIG", "openai")
    monkeypatch.setenv("LLM_SMALL", "openai")
    monkeypatch.setenv("IMAGE", "openai")
    monkeypatch.setenv("EMBEDDING", "grok")

    cfg = importlib.reload(config_module)

    assert cfg.config.EMBEDDING == "grok"


def test_config_uses_model_overrides(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_MODEL_LLM_BIG", "my-big-model")
    monkeypatch.setenv("OPENAI_MODEL_LLM_SMALL", "my-small-model")
    monkeypatch.setenv("OPENAI_MODEL_IMG_BASE", "my-image-model")
    monkeypatch.setenv("OPENAI_MODEL_EMBEDDING", "my-embedding-model")
    monkeypatch.setenv("GROK_MODEL_LLM_BIG", "my-grok-big")
    monkeypatch.setenv("GROK_MODEL_LLM_SMALL", "my-grok-small")
    monkeypatch.setenv("GROK_MODEL_LLM_IMG_BASE", "my-grok-image")
    monkeypatch.setenv("GROK_MODEL_EMBEDDING", "my-grok-embedding")

    cfg = importlib.reload(config_module)

    assert cfg.config.OPENAI_MODEL_LLM_BIG == "my-big-model"
    assert cfg.config.OPENAI_MODEL_LLM_SMALL == "my-small-model"
    assert cfg.config.OPENAI_MODEL_IMG_BASE == "my-image-model"
    assert cfg.config.OPENAI_MODEL_EMBEDDING == "my-embedding-model"
    assert cfg.config.GROK_MODEL_LLM_BIG == "my-grok-big"
    assert cfg.config.GROK_MODEL_LLM_SMALL == "my-grok-small"
    assert cfg.config.GROK_MODEL_LLM_IMG_BASE == "my-grok-image"
    assert cfg.config.GROK_MODEL_EMBEDDING == "my-grok-embedding"

