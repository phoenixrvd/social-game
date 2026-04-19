from __future__ import annotations

from engine.services.scene_service import SceneService
from engine.tools.abstract_job import AbstractJob
from engine.config import config


class SceneJob(AbstractJob):
    def __init__(self) -> None:
        self.rate_limit_seconds = config.UPDATER_SCENE_CHECK_INTERVAL_SECONDS
        self._service = SceneService()

    def execute(self) -> None:
        self._service.run_update()

