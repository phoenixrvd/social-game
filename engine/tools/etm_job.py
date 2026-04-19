from __future__ import annotations

from engine.services.etm_service import EtmService
from engine.tools.abstract_job import AbstractJob
from engine.config import config


class EtmJob(AbstractJob):
    def __init__(self) -> None:
        self.rate_limit_seconds = config.UPDATER_ETM_CHECK_INTERVAL_SECONDS
        self._service = EtmService()

    def execute(self) -> None:
        self._service.compress_stm()

