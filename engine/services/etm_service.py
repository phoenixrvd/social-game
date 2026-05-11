from __future__ import annotations

from engine.client import client
from engine.config import config
from engine.services.lightrag_memory import LightRagMemory
from engine.storage import storage

EMPTY_ETM_TEXT = "(keine zusätzlichen relevanten Erinnerungen)"


class EtmService:
    def compress_stm(self) -> str:
        batch_messages = storage.npc.stm.batch_messages()
        if not batch_messages:
            return ""

        batch_text = storage.npc.stm.batch_text_short
        episode = self._create_episode(batch_text)
        self._store_etm_text(episode)
        storage.npc.stm.remove(batch_messages)
        return episode

    def load_relevant(self, query_text: str) -> str:
        context = self._query_etm_text(query_text)
        if not context:
            return EMPTY_ETM_TEXT
        return context

    @staticmethod
    def _create_episode(stm_text: str) -> str:
        prompt = (
            storage.prompts.etm_update.get()
            .strip()
            .replace("{{SHORT_TERM_MEMORY}}", stm_text)
        )
        return client.run_prompt_small(prompt).strip()

    def _store_etm_text(self, text: str) -> None:
        cleaned_text = text.strip()
        if not cleaned_text:
            return
        self._memory().insert(cleaned_text)

    def _query_etm_text(self, query_text: str) -> str:
        return self._memory().query_context(query_text, config.ETM_RETRIEVAL_TOP_K)

    @staticmethod
    def _memory() -> LightRagMemory:
        return LightRagMemory(storage.npc.etm_dir)
