from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

_NPC_SUBDIR = "npcs"
_SCENE_SUBDIR = "scenes"
Provider = Literal["openai", "grok"]


class Config(BaseSettings):
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
    NPC_DIR: Path = PROJECT_ROOT / _NPC_SUBDIR
    SCENE_DIR: Path = PROJECT_ROOT / _SCENE_SUBDIR
    DATA_DIR: Path = PROJECT_ROOT / ".data"
    DATA_NPC_DIR: Path = DATA_DIR / _NPC_SUBDIR
    SESSION_PATH: Path = DATA_DIR / "session.yaml"
    OVERRIDES_DIR: Path = PROJECT_ROOT / ".overrides"
    OVERRIDES_NPC_DIR: Path = OVERRIDES_DIR / _NPC_SUBDIR
    OVERRIDES_SCENE_DIR: Path = OVERRIDES_DIR / _SCENE_SUBDIR
    OVERRIDES_PROMPTS_DIR: Path = OVERRIDES_DIR / "prompts"

    # Episodic Term Memory (ETM) configuration
    # Anzahl der neuesten Short-Term-Memory-Nachrichten, die im STM bleiben sollen
    UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP: int = 20
    # Schwellwert für die Anzahl älterer STM-Nachrichten, ab dem ETM-Episoden erstellt werden
    UPDATER_ETM_BATCH_SIZE_THRESHOLD: int = 7
    # Anzahl der ETM-Episoden, die im Retrieval zusätzlich in den Prompt geladen werden
    ETM_RETRIEVAL_TOP_K: int = 4
    # Maximale Cosine-Distance für ETM-Retrieval-Treffer, kleiner ist relevanter
    ETM_RETRIEVAL_MAX_DISTANCE: float = 0.75
    # Anzahl der letzten STM-Nachrichten, die als Kontext in die ETM-Query einfließen
    ETM_RETRIEVAL_QUERY_LAST_N_STM_MESSAGES: int = 5

    # Anzahl der letzten Nachrichten die für State-Updates berücksichtigt werden
    STATE_AUTO_TRIGGER_LAST_N_MESSAGES: int = 5

    # Orchestrator updater interval defaults (seconds)
    UPDATER_ETM_CHECK_INTERVAL_SECONDS: int = 350
    UPDATER_SCENE_CHECK_INTERVAL_SECONDS: int = 30
    UPDATER_STATE_CHECK_INTERVAL_SECONDS: int = 30
    UPDATER_IMAGE_CHECK_INTERVAL_SECONDS: int = 60

    # Web GUI
    WEB_DEBUG: bool = False

    # LLM configuration
    LLM_BIG: Provider = "openai"
    LLM_SMALL: Provider = "openai"
    IMAGE: Provider = "openai"
    EMBEDDING: Provider = "openai"

    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None
    OPENAI_MODEL_LLM_BIG: str = "gpt-5.4"
    OPENAI_MODEL_LLM_SMALL: str = "gpt-5.4-mini"
    OPENAI_MODEL_IMG_BASE: str = "gpt-image-1.5"
    OPENAI_MODEL_EMBEDDING: str = "text-embedding-3-small"

    GROK_API_KEY: str | None = None
    GROK_BASE_URL: str = "https://api.x.ai/v1"
    GROK_MODEL_LLM_BIG: str = "grok-4.20-0309-non-reasoning"
    GROK_MODEL_LLM_SMALL: str = "grok-4-1-fast-non-reasoning"
    GROK_MODEL_LLM_IMG_BASE: str = "grok-imagine-image"
    GROK_MODEL_EMBEDDING: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


config = Config()
