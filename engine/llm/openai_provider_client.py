from __future__ import annotations

import base64
from io import BytesIO
from typing import Iterator

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from engine.config import config
from engine.llm.provider_client import NamedImage, ProviderClient


class OpenAiProviderClient(ProviderClient):
    @property
    def _provider_name(self) -> str:
        return "OpenAI"

    def request_big(
        self,
        messages: list[ChatCompletionMessageParam],
    ) -> Iterator[str]:
        return self._chat_request(
            config.OPENAI_MODEL_LLM_BIG,
            messages,
        )

    def request_small(
        self,
        messages: list[ChatCompletionMessageParam],
    ) -> str:
        chunks = self._chat_request(
            config.OPENAI_MODEL_LLM_SMALL,
            messages,
        )
        return "".join(chunks)

    def request_image(
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
        encoded_image = result.data[0].b64_json
        if encoded_image is None:
            raise RuntimeError("OpenAI-Bildantwort enthaelt kein Bildpayload.")
        return base64.b64decode(encoded_image)

    def request_embeddings(self, texts: list[str]) -> list[list[float]]:
        response = self._request(
            lambda openai_client: openai_client.embeddings.create(model=config.OPENAI_MODEL_EMBEDDING, input=texts)
        )
        return [item.embedding for item in response.data]

    @staticmethod
    def _text_client() -> OpenAI:
        return OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL) if config.OPENAI_BASE_URL else OpenAI(api_key=config.OPENAI_API_KEY)



