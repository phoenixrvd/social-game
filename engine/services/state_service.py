from __future__ import annotations

from engine.client import client
from engine.services.etm_service import EtmService
from engine.storage import storage


class StateService:
    def __init__(self) -> None:
        self.etm_retrieval = EtmService()

    def run_update(self) -> str:
        prompt = self._build_prompt()
        state = client.run_prompt_small(prompt).strip()

        storage.npc.state_runtime.save(state)
        return state

    def _build_prompt(self) -> str:
        stm_text = storage.npc.stm.text
        etm_text = self.etm_retrieval.load_relevant(stm_text)
        return (
            storage.prompts.state_update.get().strip()
            .replace("{{CURRENT_STATE}}", storage.npc.state)
            .replace("{{SHORT_TERM_MEMORY}}", stm_text)
            .replace("{{CURRENT_ETM}}", etm_text)
        )
