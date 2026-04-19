from __future__ import annotations

from engine.llm.client import client
from engine.services.etm_service import EtmService
from engine.storage import storage
from engine.stores.npc_store import NpcStore


class StateService:
    def __init__(self) -> None:
        self.etm_retrieval = EtmService()
        self._npc_store = NpcStore()

    def run_update(self) -> str:
        prompt = self._build_prompt()
        state = client.run_prompt_small(prompt).strip()

        storage.npc.state_runtime.save(state)
        return state

    def _build_prompt(self) -> str:
        npc = self._npc_store.load()
        stm_text = npc.stm.as_string_long()
        etm_text = self.etm_retrieval.load_relevant(stm_text)
        return (
            storage.prompts.state_update.get().strip()
            .replace("{{CURRENT_STATE}}", npc.state)
            .replace("{{SHORT_TERM_MEMORY}}", stm_text)
            .replace("{{CURRENT_ETM}}", etm_text)
        )

