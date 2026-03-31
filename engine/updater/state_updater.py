from __future__ import annotations

from engine.logging import get_logger, log_info
from engine.config import config
from engine.fs_utils import load_text
from engine.llm_client import run_prompt_small
from engine.stores.npc_store import NpcStore
from engine.updater.image_updater import ImageUpdater
from engine.updater.updater import AbstractUpdater

STATE_PROMPT_PATH = config.PROJECT_ROOT / "prompts" / "state_update.md"
LOGGER = get_logger("updater.state")


class StateUpdater(AbstractUpdater):

    def __init__(self) -> None:
        self.npc_store = NpcStore()
        self.image_updater = ImageUpdater()

    def get_update_interval(self) -> int:
        return config.UPDATER_STATE_CHECK_INTERVAL_SECONDS

    def schedule(self) -> None:
        npc = self.npc_store.load()

        if not self._should_run_for_npc(npc):
            log_info(LOGGER, "updater_active", updater="state", active=False, prompt_start=False, reason="no_new_messages", stm_count=len(npc.stm))
            return

        log_info(LOGGER, "updater_active", updater="state", active=True, prompt_start=True, stm_count=len(npc.stm))
        prompt = (
            load_text(STATE_PROMPT_PATH).strip()
            .replace("{{CURRENT_STATE}}", npc.state)
            .replace("{{SHORT_TERM_MEMORY}}", self.format_short_memory(npc.stm))
            .replace("{{LONG_TERM_MEMORY}}", npc.ltm.strip() or "(leer)")
        )
        raw = run_prompt_small(prompt).strip()

        self.npc_store.save_state(npc.npc_id, npc.scene.scene_id, raw)
        self.image_updater.emit_update()

        log_info(LOGGER, "updater_completed", updater="state", state_length=len(raw))