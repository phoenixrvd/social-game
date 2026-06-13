from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Config(BaseSettings):
    # Paths
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
    NPC_DIR: Path = PROJECT_ROOT / "npcs"
    AVATAR_DIR: Path = PROJECT_ROOT / "avatars"
    SCENE_DIR: Path = PROJECT_ROOT / "scenes"
    DATA_DIR: Path = PROJECT_ROOT / ".data"
    DATA_NPC_DIR: Path = DATA_DIR / "npcs"
    SESSION_PATH: Path = DATA_DIR / "session.yaml"
    OVERRIDES_NPC_DIR: Path = PROJECT_ROOT / ".overrides" / "npcs"
    OVERRIDES_AVATAR_DIR: Path = PROJECT_ROOT / ".overrides" / "avatars"
    OVERRIDES_SCENE_DIR: Path = PROJECT_ROOT / ".overrides" / "scenes"
    OVERRIDES_PROMPTS_DIR: Path = PROJECT_ROOT / ".overrides" / "prompts"

    # Defaults
    DEFAULT_NPC_ID: str = "vika"
    DEFAULT_AVATAR_ID: str = "max"
    DEFAULT_SCENE_ID: str = "office"

    # Episodic Term Memory (ETM) configuration
    UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP: int = 20
    UPDATER_ETM_BATCH_SIZE_THRESHOLD: int = 7
    ETM_RETRIEVAL_TOP_K: int = 4

    # Short-Term Memory (STM)
    STM_LATEST_MESSAGES: int = 5

    # Updater intervals
    UPDATER_ETM_CHECK_INTERVAL_SECONDS: int = 350
    UPDATER_SCENE_CHECK_INTERVAL_SECONDS: int = 30
    UPDATER_STATE_CHECK_INTERVAL_SECONDS: int = 30
    UPDATER_IMAGE_CHECK_INTERVAL_SECONDS: int = 60

    # Web
    WEB_DEBUG: bool = False

    # LLM
    MODEL_API_KEY: str = "none"
    MODEL_BASE_URL: str = "https://api.openai.com/v1"
    MODEL_LLM_BIG: str = "gpt-5.4"
    MODEL_LLM_SMALL: str = "gpt-5.4-mini"
    MODEL_IMAGE: str = "gpt-image-1.5"
    MODEL_EMBEDDING: str = "text-embedding-3-small"
    MODEL_EMBEDDING_DIMENSIONS: int = 1536
    MODEL_EMBEDDING_MAX_TOKENS: int = 8192
    MODEL_VERIFY_SSL: bool = True
    MODEL_TIMEOUT_SECONDS: float = 60.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SG_",
        extra="ignore",
    )


config = Config()
