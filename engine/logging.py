from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock
from typing import Any

from engine.config import config

LOGGER_NAME = "social_game"
_CONFIG_LOCK = Lock()


class CustomRotatingFileHandler(RotatingFileHandler):
    """RotatingFileHandler mit app.1.log Naming statt app.log.1"""
    
    def rotation_filename(self, default_name: str) -> str:
        """Generiert app.1.log statt app.log.1"""
        # default_name ist z.B. "/path/to/app.log.1"
        path = Path(default_name)
        # Extrahiere die Nummer
        parts = path.name.split('.')
        if len(parts) >= 2 and parts[-1].isdigit():
            number = parts[-1]
            stem = '.'.join(parts[:-2])  # alles außer .log.1
            return str(path.parent / f"{stem}.{number}.log")
        return default_name


class StructuredLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if isinstance(record.msg, dict):
            original_msg = record.msg
            original_args = record.args
            record.msg = json.dumps(original_msg, ensure_ascii=False, indent=2, default=str)
            record.args = ()
            try:
                return super().format(record)
            finally:
                record.msg = original_msg
                record.args = original_args

        return super().format(record)


def _configure_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)

    if getattr(logger, "_social_game_configured", False):
        return logger

    with _CONFIG_LOCK:
        if getattr(logger, "_social_game_configured", False):
            return logger

        config.APP_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Log rotation based on config: APP_LOG_MAX_SIZE_MB and APP_LOG_BACKUP_COUNT
        max_bytes = config.APP_LOG_MAX_SIZE_MB * 1024 * 1024
        handler = CustomRotatingFileHandler(
            config.APP_LOG_PATH,
            encoding="utf-8",
            maxBytes=max_bytes,
            backupCount=config.APP_LOG_BACKUP_COUNT
        )
        formatter = StructuredLogFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        resolved_level = getattr(logging, str(config.LOG_LEVEL).upper(), logging.INFO)
        logger.setLevel(resolved_level)

        if config.LOG_SHOW_IN_CLI:
            cli_handler = logging.StreamHandler()
            cli_handler.setFormatter(formatter)
            logger.addHandler(cli_handler)

        logger.propagate = False
        logger._social_game_configured = True  # type: ignore[attr-defined]

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    base_logger = _configure_logger()
    if not name:
        return base_logger

    return base_logger.getChild(name)


def log_info(logger: logging.Logger, event: str, /, **payload: Any) -> None:
    logger.info({"event": event, **payload})




