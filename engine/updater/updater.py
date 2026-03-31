from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.config import config
from engine.fs_utils import load_text, save_text
from engine.models import Npc, ShortMemoryMessage

UNINITIALIZED_CHECK_TIME = datetime.min.replace(tzinfo=UTC)


class AbstractUpdater(ABC):
    npc_store: Any

    @staticmethod
    def format_short_memory(messages: list[ShortMemoryMessage], last_n: int | None = None) -> str:
        if not messages:
            return "(keine Nachrichten)"

        selected = messages[-last_n:] if last_n is not None else messages
        lines = []
        for m in selected:
            lines.append(f"{m.role[0].upper()}: {m.content.strip()}")

        return "\n".join(lines)

    def _current_npc_scene_data_dir(self) -> Path:
        npc = self.npc_store.load()
        path = config.DATA_NPC_DIR / npc.npc_id / npc.scene.scene_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _orchestrator_dir(self) -> Path:
        path = self._current_npc_scene_data_dir() / "orchestrator"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _last_check_path(self) -> Path:
        module_file_prefix = self.__class__.__module__.rpartition(".")[2]
        return self._orchestrator_dir() / f"{module_file_prefix}_last_check.txt"

    @staticmethod
    def _load_last_check(path: Path) -> datetime:
        if not path.exists():
            return UNINITIALIZED_CHECK_TIME

        return datetime.fromisoformat(load_text(path).strip())

    @staticmethod
    def _save_last_check(path: Path) -> None:
        save_text(path, datetime.now(UTC).isoformat())

    def _should_run_for_npc(self, npc: Npc) -> bool:
        last_check_path = self._last_check_path()
        last_check = self._load_last_check(last_check_path)

        if not npc.has_messages_after(last_check):
            return False

        self._save_last_check(last_check_path)
        return True

    @abstractmethod
    def get_update_interval(self) -> int:
        ...

    @abstractmethod
    def schedule(self) -> None:
        ...
