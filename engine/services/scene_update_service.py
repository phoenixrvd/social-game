from __future__ import annotations

from engine.config import config
from engine.llm.client import run_prompt_small
from engine.models import Npc
from engine.services.etm_retrieval_service import EtmRetrievalService
from engine.services.memory_format import format_update_memory
from engine.storage import storage
from engine.updater.image_updater import ImageUpdater


class SceneUpdateService:
    def __init__(self) -> None:
        self.image_updater = ImageUpdater()
        self.etm_retrieval = EtmRetrievalService()

    def run(self, npc: Npc) -> str:
        prompt = self._build_prompt(npc)
        scene = run_prompt_small(prompt).strip()

        storage.scene.scene_runtime.save(scene)
        self.image_updater.emit_update()
        return scene

    def _build_prompt(self, npc: Npc) -> str:
        stm = npc.stm[-config.STATE_AUTO_TRIGGER_LAST_N_MESSAGES:]
        stm_text = format_update_memory(stm)
        etm_text = self.etm_retrieval.load_relevant(npc, stm_text)
        return (
            storage.prompts.scene_update.get().strip()
            .replace("{{SCENE_DATA}}", npc.scene.description.strip())
            .replace("{{SHORT_TERM_MEMORY}}", stm_text)
            .replace("{{CURRENT_ETM}}", etm_text)
        )
