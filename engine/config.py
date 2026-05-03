from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

_NPC_SUBDIR = "npcs"
_SCENE_SUBDIR = "scenes"


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

    DEFAULT_NPC_ID: str = "vika"
    DEFAULT_SCENE_ID: str = "office"

    # Episodic Term Memory (ETM) configuration
    # Anzahl der neuesten Short-Term-Memory-Nachrichten, die im STM bleiben sollen
    UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP: int = 20
    # Schwellwert für die Anzahl älterer STM-Nachrichten, ab dem ETM-Episoden erstellt werden
    UPDATER_ETM_BATCH_SIZE_THRESHOLD: int = 7
    # Anzahl der ETM-Episoden, die im Retrieval zusätzlich in den Prompt geladen werden
    ETM_RETRIEVAL_TOP_K: int = 4
    # Maximale Cosine-Distance für ETM-Retrieval-Treffer, kleiner ist relevanter
    ETM_RETRIEVAL_MAX_DISTANCE: float = 0.75

    # Anzahl der letzten STM-Nachrichten für allgemeine Latest-Properties im Storage
    STM_LATEST_MESSAGES: int = 5

    # Orchestrator updater interval defaults (seconds)
    UPDATER_ETM_CHECK_INTERVAL_SECONDS: int = 350
    UPDATER_SCENE_CHECK_INTERVAL_SECONDS: int = 30
    UPDATER_STATE_CHECK_INTERVAL_SECONDS: int = 30
    UPDATER_IMAGE_CHECK_INTERVAL_SECONDS: int = 60

    # Web GUI
    WEB_DEBUG: bool = False

    # LLM configuration
    MODEL_API_KEY: str = "none"
    MODEL_BASE_URL: str = "https://api.openai.com/v1"
    MODEL_LLM_BIG: str = "gpt-5.4"
    MODEL_LLM_SMALL: str = "gpt-5.4-mini"
    MODEL_IMAGE: str = "gpt-image-1.5"
    MODEL_EMBEDDING: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SG_",
        extra="ignore",
    )


config = Config()
