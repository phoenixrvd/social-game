from __future__ import annotations

from engine.logging import get_logger, log_info
from engine.config import config
from engine.fs_utils import load_text
from engine.llm_client import run_prompt
from engine.stores.npc_store import NpcStore
from engine.updater.image_updater import ImageUpdater
from engine.updater.updater import AbstractUpdater

LOGGER = get_logger("updater.scene")


class SceneUpdater(AbstractUpdater):

    def __init__(self) -> None:
        self.npc_store = NpcStore()
        self.image_updater = ImageUpdater()

    def get_update_interval(self) -> int:
        return config.UPDATER_SCENE_CHECK_INTERVAL_SECONDS

    def schedule(self) -> None:
        npc = self.npc_store.load()

        if not self._should_run_for_npc(npc):
            log_info(LOGGER, "updater_active", updater="scene", active=False, prompt_start=False, reason="no_new_messages", stm_count=len(npc.stm))
            return

        log_info(LOGGER, "updater_active", updater="scene", active=True, prompt_start=True, stm_count=len(npc.stm))
        stm = npc.stm[-config.STATE_AUTO_TRIGGER_LAST_N_MESSAGES:]

        prompt = (
            load_text(config.PROJECT_ROOT / "prompts" / "scene_update.md").strip()
            .replace("{{SCENE_DATA}}", npc.scene.description.strip())
            .replace("{{SHORT_TERM_MEMORY}}", self.format_short_memory(stm))
            .replace("{{LONG_TERM_MEMORY}}", npc.ltm.strip() or "(leer)")
        )
        raw_scene = run_prompt(prompt, model=config.MODEL_LLM_SMALL).strip()

        self.npc_store.save_scene(raw_scene)
        self.image_updater.emit_update()

        log_info(LOGGER, "updater_completed", updater="scene", scene_length=len(raw_scene))
