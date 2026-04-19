from __future__ import annotations

from engine.services.image_service import ImageService
from engine.tools.abstract_job import AbstractJob
from engine.config import config


class ImageJob(AbstractJob):
    def __init__(self) -> None:
        self.rate_limit_seconds = config.UPDATER_IMAGE_CHECK_INTERVAL_SECONDS
        self._service = ImageService()

    def execute(self) -> None:
        self._service.update_from_context()

