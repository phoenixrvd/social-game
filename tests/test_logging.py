from __future__ import annotations

import logging

import engine.logging as logging_module


def _reset_test_logger() -> tuple[logging.Logger, list[logging.Handler], int, bool, bool]:
    logger = logging.getLogger(logging_module.LOGGER_NAME)
    saved_handlers = list(logger.handlers)
    saved_level = logger.level
    saved_propagate = logger.propagate
    saved_configured = getattr(logger, "_social_game_configured", False)

    for handler in saved_handlers:
        logger.removeHandler(handler)

    if hasattr(logger, "_social_game_configured"):
        delattr(logger, "_social_game_configured")

    return logger, saved_handlers, saved_level, saved_propagate, saved_configured


def _restore_test_logger(
    logger: logging.Logger,
    saved_handlers: list[logging.Handler],
    saved_level: int,
    saved_propagate: bool,
    saved_configured: bool,
) -> None:
    new_handlers = list(logger.handlers)
    for handler in new_handlers:
        logger.removeHandler(handler)
        handler.close()

    for handler in saved_handlers:
        logger.addHandler(handler)

    logger.setLevel(saved_level)
    logger.propagate = saved_propagate
    logger._social_game_configured = saved_configured  # type: ignore[attr-defined]


def test_logger_writes_dict_as_pretty_multiline_json(tmp_path, monkeypatch):
    log_path = tmp_path / "app.log"
    monkeypatch.setattr(logging_module.config, "APP_LOG_PATH", log_path)
    logger, saved_handlers, saved_level, saved_propagate, saved_configured = _reset_test_logger()

    try:
        test_logger = logging_module.get_logger("test")
        logging_module.log_info(test_logger, "demo_event", active=False, reason="inactive", nested={"a": 1})
    finally:
        _restore_test_logger(logger, saved_handlers, saved_level, saved_propagate, saved_configured)

    content = log_path.read_text(encoding="utf-8")
    assert '"event": "demo_event"' in content
    assert '"active": false' in content
    assert '"reason": "inactive"' in content
    assert '"nested": {' in content


def test_logger_writes_exception_as_is(tmp_path, monkeypatch):
    log_path = tmp_path / "app.log"
    monkeypatch.setattr(logging_module.config, "APP_LOG_PATH", log_path)
    logger, saved_handlers, saved_level, saved_propagate, saved_configured = _reset_test_logger()

    try:
        test_logger = logging_module.get_logger("test")
        try:
            raise ValueError("kaputt\nmehrzeilig")
        except ValueError:
            test_logger.exception("fehler\nbeim update")
    finally:
        _restore_test_logger(logger, saved_handlers, saved_level, saved_propagate, saved_configured)

    content = log_path.read_text(encoding="utf-8")
    assert "fehler\nbeim update" in content
    assert "Traceback (most recent call last)" in content
    assert "ValueError: kaputt\nmehrzeilig" in content




