from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from engine.models import Npc
from engine.storage import storage
from engine.stores.npc_store import NpcStore

UNINITIALIZED_CHECK_TIME = datetime.min.replace(tzinfo=UTC)


class AbstractUpdater(ABC):
    npc_store: NpcStore

    def _last_check_item(self, npc: Npc):
        module_file_prefix = self.__class__.__module__.rpartition(".")[2]
        npc_paths = storage.npc_view(npc_id=npc.npc_id, scene_id=npc.scene.scene_id)
        return npc_paths.orchestrator_text(f"{module_file_prefix}_last_check.txt")

    @staticmethod
    def _load_last_check(item) -> datetime:
        if not item.exists():
            return UNINITIALIZED_CHECK_TIME

        return datetime.fromisoformat(item.get().strip())

    @staticmethod
    def _save_last_check(item) -> None:
        item.save(datetime.now(UTC).isoformat())

    def _should_run_for_npc(self, npc: Npc) -> bool:
        last_check_item = self._last_check_item(npc)
        last_check = self._load_last_check(last_check_item)

        if not npc.has_messages_after(last_check):
            return False

        self._save_last_check(last_check_item)
        return True

    @staticmethod
    @abstractmethod
    def get_update_interval() -> int:
        ...

    @abstractmethod
    def schedule(self) -> None:
        ...
