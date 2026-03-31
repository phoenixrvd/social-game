from __future__ import annotations

from engine.logging import get_logger, log_info
from engine.config import config
from engine.fs_utils import load_text
from engine.llm_client import run_prompt_small
from engine.stores.npc_store import NpcStore
from engine.updater.updater import AbstractUpdater

LTM_PROMPT_PATH = config.PROJECT_ROOT / "prompts" / "ltm_summary.md"
LOGGER = get_logger("updater.ltm")


class LtmUpdater(AbstractUpdater):

    def __init__(self) -> None:
        self.npc_store = NpcStore()

    def get_update_interval(self) -> int:
        return config.UPDATER_LTM_CHECK_INTERVAL_SECONDS

    def schedule(self) -> None:
        npc = self.npc_store.load()
        batch = npc.stm[:-config.UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP]

        if len(batch) <= config.UPDATER_LTM_BATCH_SIZE_THRESHOLD:
            log_info(LOGGER, "updater_active", updater="ltm", active=False, prompt_start=False, reason="batch_too_small", batch_size=len(batch))
            return

        if not self._should_run_for_npc(npc):
            log_info(LOGGER, "updater_active", updater="ltm", active=False, prompt_start=False, reason="no_new_messages", batch_size=len(batch))
            return

        log_info(LOGGER, "updater_active", updater="ltm", active=True, prompt_start=True, batch_size=len(batch))
        prompt = (
            load_text(LTM_PROMPT_PATH).strip()
            .replace("{{LONG_TERM_MEMORY}}", npc.ltm.strip() or "(leer)")
            .replace("{{SHORT_TERM_MEMORY}}", self.format_short_memory(batch))
        )
        updated_ltm = run_prompt_small(prompt).strip()
        batch_ids = [message.id for message in batch]

        self.npc_store.save_ltm(npc.npc_id, npc.scene.scene_id, updated_ltm)
        self.npc_store.remove_stm_by_ids(npc.npc_id, npc.scene.scene_id, batch_ids)
        log_info(LOGGER, "updater_completed", updater="ltm", ltm_length=len(updated_ltm), removed_stm=len(batch_ids))
