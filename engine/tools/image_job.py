from __future__ import annotations

from engine.logger import logger
from engine.services.image_service import ImageService
from engine.tools.abstract_job import AbstractJob
from engine.config import config


class ImageJob(AbstractJob):
    def __init__(self) -> None:
        self.rate_limit_seconds = config.UPDATER_IMAGE_CHECK_INTERVAL_SECONDS
        self._service = ImageService()

    def execute(self) -> None:
        from engine.storage.facade import storage
        if not storage.session.image_autogenerate:
            logger.info("Automatische Bildgenerierung deaktiviert – ImageJob wird übersprungen.")
            return
        self._service.update_from_context()

