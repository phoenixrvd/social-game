from __future__ import annotations

from engine.config import config
from engine.services.user_profile_service import UserProfileService
from engine.tools.abstract_job import AbstractJob


class UserProfileJob(AbstractJob):
    def __init__(self) -> None:
        self.rate_limit_seconds = config.UPDATER_USER_PROFILE_CHECK_INTERVAL_SECONDS
        self._service = UserProfileService()

    def execute(self) -> None:
        self._service.run_update()
