from __future__ import annotations

from engine.config import config
from engine.services.etm_update_service import EtmUpdateService
from engine.updater.updater import AbstractUpdater


class EtmUpdater(AbstractUpdater):
    def __init__(self) -> None:
        self.service = EtmUpdateService()
        self.npc_store = self.service.npc_store

    @staticmethod
    def get_update_interval() -> int:
        return config.UPDATER_ETM_CHECK_INTERVAL_SECONDS

    def schedule(self) -> None:
        npc = self.npc_store.load()

        if not npc.stm.get_batch():
            return

        if not self._should_run_for_npc(npc):
            return

        self.service.run()
