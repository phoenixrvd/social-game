from __future__ import annotations

from engine.llm.client import run_prompt_small
from engine.models import Npc
from engine.services.etm_retrieval_service import EtmRetrievalService
from engine.services.memory_format import format_update_memory
from engine.storage import storage
from engine.updater.image_updater import ImageUpdater


class StateUpdateService:
    def __init__(self) -> None:
        self.image_updater = ImageUpdater()
        self.etm_retrieval = EtmRetrievalService()

    def run(self, npc: Npc) -> str:
        prompt = self._build_prompt(npc)
        state = run_prompt_small(prompt).strip()

        storage.npc.state_runtime.save(state)
        self.image_updater.emit_update()
        return state

    def _build_prompt(self, npc: Npc) -> str:
        stm_text = format_update_memory(npc.stm)
        etm_text = self.etm_retrieval.load_relevant(npc, stm_text)
        return (
            storage.prompts.state_update.get().strip()
            .replace("{{CURRENT_STATE}}", npc.state)
            .replace("{{SHORT_TERM_MEMORY}}", stm_text)
            .replace("{{CURRENT_ETM}}", etm_text)
        )
