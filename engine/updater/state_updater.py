from __future__ import annotations

from engine.config import config
from engine.services.state_update_service import StateUpdateService
from engine.stores.npc_store import NpcStore
from engine.updater.updater import AbstractUpdater


class StateUpdater(AbstractUpdater):
    def __init__(self) -> None:
        self.npc_store = NpcStore()
        self.service = StateUpdateService()

    @staticmethod
    def get_update_interval() -> int:
        return config.UPDATER_STATE_CHECK_INTERVAL_SECONDS

    def schedule(self) -> None:
        npc = self.npc_store.load()

        if not self._should_run_for_npc(npc):
            return

        self.service.run(npc)
