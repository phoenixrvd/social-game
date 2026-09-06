from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

import numpy as np
from openai.types.responses import EasyInputMessageParam, ResponseInputParam

from engine.client import client
from engine.config import config

try:
    from lightrag import LightRAG, QueryParam
    from lightrag.kg.shared_storage import finalize_share_data
    from lightrag.utils import EmbeddingFunc
except ImportError:  # pragma: no cover
    finalize_share_data = None
    LightRAG = None
    QueryParam = None
    EmbeddingFunc = None


class LightRagMemory:
    def __init__(self, working_dir: Path) -> None:
        self.working_dir = working_dir

    def insert(self, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            return
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self._run(self._insert(cleaned))

    def query_context(self, query: str, top_k: int) -> str:
        cleaned = query.strip()
        if top_k <= 0 or not cleaned or not self.working_dir.exists():
            return ""
        return str(self._run(self._query_context(cleaned, top_k))).strip()

    async def _insert(self, text: str) -> None:
        rag = await self._create_rag()
        try:
            await rag.ainsert(text)
        finally:
            await rag.finalize_storages()
            self._finalize_shared_storage()

    async def _query_context(self, query: str, top_k: int) -> str:
        rag = await self._create_rag()
        try:
            param = QueryParam(
                mode="mix",
                only_need_context=True,
                top_k=top_k,
                enable_rerank=False,
            )
            return await rag.aquery(query, param=param)
        finally:
            await rag.finalize_storages()
            self._finalize_shared_storage()

    async def _create_rag(self) -> Any:
        if LightRAG is None or EmbeddingFunc is None:
            raise RuntimeError(
                "LightRAG ist nicht installiert. Bitte `lightrag-hku` installieren."
            )

        rag = LightRAG(
            working_dir=str(self.working_dir),
            llm_model_func=self._llm_model_func,
            llm_model_name=config.MODEL_LLM_SMALL,
            embedding_func=EmbeddingFunc(
                embedding_dim=config.MODEL_EMBEDDING_DIMENSIONS,
                max_token_size=config.MODEL_EMBEDDING_MAX_TOKENS,
                model_name=config.MODEL_EMBEDDING,
                func=self._embedding_func,
            ),
            enable_llm_cache=False,
        )
        await rag.initialize_storages()
        return rag

    @staticmethod
    async def _llm_model_func(
        prompt: str,
        system_prompt: str | None = None,
        history_messages: list[dict[str, str]] | None = None,
        **_kwargs: Any,
    ) -> str:
        messages: ResponseInputParam = []
        if system_prompt:
            messages.append(EasyInputMessageParam(role="system", content=system_prompt))
        for message in history_messages or []:
            messages.append(cast(EasyInputMessageParam, message))
        messages.append(EasyInputMessageParam(role="user", content=prompt))
        return client.run_messages_small(messages)

    @staticmethod
    async def _embedding_func(texts: list[str]) -> np.ndarray:
        embeddings = [client.embed_texts(text) for text in texts]
        return np.array(embeddings, dtype=np.float32)

    @staticmethod
    def _finalize_shared_storage() -> None:
        if finalize_share_data is not None:
            finalize_share_data()

    @staticmethod
    def _run(coroutine):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)
        coroutine.close()
        raise RuntimeError(
            "LightRAG-Operationen duerfen nicht aus einem laufenden Event-Loop synchron gestartet werden."
        )
