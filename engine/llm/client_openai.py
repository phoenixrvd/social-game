from __future__ import annotations

import base64
from io import BytesIO
from typing import Callable, Iterable, Iterator, TypeVar

import openai
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from engine.config import config
from engine.llm.client_interface import ClientInterface, NamedImage
from engine.llm.error_utils import llm_error_message

T = TypeVar("T")


class ClientOpenAi(ClientInterface):
    def big_request(
        self,
        messages: list[ChatCompletionMessageParam],
        *,
        stream: bool,
    ) -> str | Iterator[str]:
        return self._chat_request(config.OPENAI_MODEL_LLM_BIG, messages, stream=stream)

    def small_request(
        self,
        messages: list[ChatCompletionMessageParam],
    ) -> str:
        return self._chat_request(config.OPENAI_MODEL_LLM_SMALL, messages, stream=False)

    def image_request(
        self,
        prompt: str,
        images: list[NamedImage],
    ) -> bytes:
        payload = []
        for name, image_bytes in images:
            image_file = BytesIO(image_bytes)
            image_file.name = name
            payload.append(image_file)
        image_arg: BytesIO | list[BytesIO] = payload[0] if len(payload) == 1 else payload
        result = self._request(
            lambda client: client.images.edit(
                model=config.OPENAI_MODEL_IMG_BASE,
                image=image_arg,
                prompt=prompt,
                n=1,
                size="1024x1536",
                quality="low",
                background="auto",
                input_fidelity="low",
                extra_query={"moderation": "low"},
                extra_body={"moderation": "low"},
            )
        )
        return base64.b64decode(result.data[0].b64_json)

    def embedding_request(self, texts: list[str]) -> list[list[float]]:
        response = self._request(
            lambda client: client.embeddings.create(model=config.OPENAI_MODEL_EMBEDDING, input=texts)
        )
        return [item.embedding for item in response.data]

    def _chat_request(
        self,
        model: str,
        messages: list[ChatCompletionMessageParam],
        *,
        stream: bool,
    ) -> str | Iterator[str]:
        response = self._request(
            lambda client: client.chat.completions.create(
                model=model,
                store=False,
                messages=messages,
                stream=stream,
            )
        )
        return self._stream_chunks(response) if stream else response.choices[0].message.content or ""

    def _request(self, action: Callable[[OpenAI], T]) -> T:
        try:
            return action(self._client())
        except openai.OpenAIError as exc:
            raise RuntimeError(llm_error_message(exc, "OpenAI")) from exc

    @staticmethod
    def _stream_chunks(stream: Iterable[object]) -> Iterator[str]:
        try:
            for chunk in stream:
                choices = getattr(chunk, "choices", None)
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                delta_text = getattr(delta, "content", None)
                if isinstance(delta_text, str) and delta_text:
                    yield delta_text
        except openai.OpenAIError as exc:
            raise RuntimeError(llm_error_message(exc, "OpenAI")) from exc

    @staticmethod
    def _client() -> OpenAI:
        return OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL) if config.OPENAI_BASE_URL else OpenAI(api_key=config.OPENAI_API_KEY)

