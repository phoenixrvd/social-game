from __future__ import annotations

from engine.logging import get_logger, log_info
from engine.config import config
from engine.fs_utils import load_text
from engine.llm_client import run_prompt
from engine.stores.npc_store import NpcStore
from engine.updater.updater import AbstractUpdater

LOGGER = get_logger("updater.ltm")


class LtmUpdater(AbstractUpdater):

    def __init__(self) -> None:
        self.npc_store = NpcStore()

    def get_update_interval(self) -> int:
        return config.UPDATER_LTM_CHECK_INTERVAL_SECONDS

    def schedule(self) -> None:
        npc = self.npc_store.load()
        batch = npc.stm[:-config.UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP]
        batch_size = len(batch)

        if batch_size <= config.UPDATER_LTM_BATCH_SIZE_THRESHOLD:
            log_info(LOGGER, "updater_active", updater="ltm", active=False, prompt_start=False, reason="batch_too_small", batch_size=batch_size)
            return

        if not self._should_run_for_npc(npc):
            log_info(LOGGER, "updater_active", updater="ltm", active=False, prompt_start=False, reason="no_new_messages", batch_size=batch_size)
            return

        log_info(LOGGER, "updater_active", updater="ltm", active=True, prompt_start=True, batch_size=batch_size)
        prompt = (
            load_text(config.PROJECT_ROOT / "prompts" / "ltm_summary.md").strip()
            .replace("{{LONG_TERM_MEMORY}}", npc.ltm.strip() or "(leer)")
            .replace("{{SHORT_TERM_MEMORY}}", self.format_short_memory(batch))
        )
        updated_ltm = run_prompt(prompt, model=config.MODEL_LLM_SMALL).strip()
        batch_ids = [message.id for message in batch]

        self.npc_store.save_ltm(updated_ltm)
        session_store = getattr(self.npc_store, "session_store", None)
        if session_store is not None and hasattr(session_store, "load"):
            session = session_store.load()
            self.npc_store.remove_stm_by_ids(session.npc_id, session.scene_id, batch_ids)
        else:
            self.npc_store.remove_stm_by_ids(npc.npc_id, npc.scene.scene_id, batch_ids)
        log_info(LOGGER, "updater_completed", updater="ltm", ltm_length=len(updated_ltm), removed_stm=len(batch_ids))
