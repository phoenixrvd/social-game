from __future__ import annotations

from engine.services.state_service import StateService
from engine.tools.abstract_job import AbstractJob
from engine.config import config


class StateJob(AbstractJob):
    def __init__(self) -> None:
        self.rate_limit_seconds = config.UPDATER_STATE_CHECK_INTERVAL_SECONDS
        self._service = StateService()

    def execute(self) -> None:
        self._service.run_update()

