from __future__ import annotations

from io import BytesIO
from typing import Iterable, Iterator

import openai
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from engine.config import config
from engine.llm.client_interface import ClientInterface, NamedImage
from engine.llm.error_utils import llm_error_message


class ClientOpenAi(ClientInterface):
    def big_request(
        self,
        messages: list[ChatCompletionMessageParam],
        *,
        stream: bool,
    ) -> str | Iterator[str]:
        try:
            response = self._client().chat.completions.create(
                model=config.OPENAI_MODEL_LLM_BIG,
                store=False,
                messages=messages,
                stream=stream,
            )
            if not stream:
                return response.choices[0].message.content or ""
            return self._stream_chunks(response)
        except openai.OpenAIError as exc:
            raise RuntimeError(llm_error_message(exc, "OpenAI")) from exc

    def small_request(
        self,
        messages: list[ChatCompletionMessageParam],
    ) -> str:
        try:
            response = self._client().chat.completions.create(
                model=config.OPENAI_MODEL_LLM_SMALL,
                store=False,
                messages=messages,
                stream=False,
            )
            return response.choices[0].message.content or ""
        except openai.OpenAIError as exc:
            raise RuntimeError(llm_error_message(exc, "OpenAI")) from exc

    def image_request(
        self,
        prompt: str,
        images: list[NamedImage],
    ) -> bytes:
        payload = [self._named_image_file(name, image_bytes) for name, image_bytes in images]
        image_arg: BytesIO | list[BytesIO] = payload[0] if len(payload) == 1 else payload

        try:
            result = self._client().images.edit(
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
        except openai.OpenAIError as exc:
            raise RuntimeError(llm_error_message(exc, "OpenAI")) from exc

        return self._decode_image_result(result)

    @staticmethod
    def _decode_image_result(result: object) -> bytes:
        import base64
        data = getattr(result, "data", None)
        if not data:
            raise ValueError("Image generation returned no data")
        b64_data = getattr(data[0], "b64_json", None)
        if not b64_data:
            raise ValueError("Image generation returned no base64 payload")
        return base64.b64decode(str(b64_data))

    def embedding_request(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self._client().embeddings.create(model=config.OPENAI_MODEL_EMBEDDING, input=texts)
            return [item.embedding for item in response.data]
        except openai.OpenAIError as exc:
            raise RuntimeError(llm_error_message(exc, "OpenAI")) from exc

    @staticmethod
    def _stream_chunks(stream: Iterable[object]) -> Iterator[str]:
        for chunk in stream:
            choices = getattr(chunk, "choices", None)
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            delta_text = getattr(delta, "content", None)
            if isinstance(delta_text, str) and delta_text:
                yield delta_text

    @staticmethod
    def _named_image_file(filename: str, image_bytes: bytes) -> BytesIO:
        image_file = BytesIO(image_bytes)
        image_file.name = filename
        return image_file

    @staticmethod
    def _client() -> OpenAI:
        if config.OPENAI_BASE_URL:
            return OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)
        return OpenAI(api_key=config.OPENAI_API_KEY)








