from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Config(BaseSettings):
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
    NPC_DIR: Path = PROJECT_ROOT / "npcs"
    SCENE_DIR: Path = PROJECT_ROOT / "scenes"
    DATA_DIR: Path = PROJECT_ROOT / ".data"
    APP_LOG_PATH: Path = DATA_DIR / "app.log"
    DATA_NPC_DIR: Path = DATA_DIR / "npcs"
    SESSION_PATH: Path = DATA_DIR / "session.yaml"

    # Long-Term Memory (LTM) configuration
    # Anzahl der neuesten Short-Term-Memory-Nachrichten, die im STM bleiben sollen
    UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP: int = 20
    # Schwellwert für die Anzahl älterer STM-Nachrichten, ab dem ein LTM-Update startet
    UPDATER_LTM_BATCH_SIZE_THRESHOLD: int = 7

    # Anzahl der letzten Nachrichten die für State-Updates berücksichtigt werden
    STATE_AUTO_TRIGGER_LAST_N_MESSAGES: int = 5

    # Orchestrator updater interval defaults (seconds)
    UPDATER_LTM_CHECK_INTERVAL_SECONDS: int = 350
    UPDATER_SCENE_CHECK_INTERVAL_SECONDS: int = 30
    UPDATER_STATE_CHECK_INTERVAL_SECONDS: int = 30
    UPDATER_IMAGE_CHECK_INTERVAL_SECONDS: int = 60

    # App logging configuration
    APP_LOG_MAX_SIZE_MB: int = 1
    APP_LOG_BACKUP_COUNT: int = 2
    LOG_LEVEL: str = "INFO"
    LOG_SHOW_IN_CLI: bool = True

    # LLM/OpenAI configuration
    OPENAI_API_KEY: str  # required
    MODEL_LLM_BIG: str = "gpt-5.4"
    MODEL_LLM_SMALL: str = "gpt-5.4-mini"
    MODEL_LLM_IMG_BASE: str = "gpt-image-1.5"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )


config = Config()


