from __future__ import annotations

from engine.config import Provider, config
from engine.llm.client_interface import ClientInterface
from engine.llm.client_grok import ClientGrok
from engine.llm.client_openai import ClientOpenAi


class ClientAdapter:
    def __init__(self) -> None:
        self._openai = ClientOpenAi()
        self._grok = ClientGrok()

    def big_client(self) -> ClientInterface:
        return self._provider_client(config.LLM_BIG)

    def small_client(self) -> ClientInterface:
        return self._provider_client(config.LLM_SMALL)

    def image_client(self) -> ClientInterface:
        return self._provider_client(config.IMAGE)

    def embedding_client(self) -> ClientInterface:
        return self._provider_client(config.EMBEDDING)

    def _provider_client(self, provider: Provider) -> ClientInterface:
        if provider == "grok":
            return self._grok
        return self._openai


