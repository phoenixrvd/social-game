from __future__ import annotations

import base64
from typing import Any, Callable, Iterator

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from engine.config import config
from engine.llm.provider_client import NamedImage, ProviderClient


class GrokProviderClient(ProviderClient):
    def __init__(self) -> None:
        self._local_embedding_fn: Callable[..., list] | None = None

    @property
    def _provider_name(self) -> str:
        return "Grok"

    def request_big(
        self,
        messages: list[ChatCompletionMessageParam],
    ) -> Iterator[str]:
        return self._chat_request(
            config.GROK_MODEL_LLM_BIG,
            messages,
        )

    def request_small(
        self,
        messages: list[ChatCompletionMessageParam],
    ) -> str:
        chunks = self._chat_request(
            config.GROK_MODEL_LLM_SMALL,
            messages,
        )
        return "".join(chunks)

    def request_image(self, prompt: str, images: list[NamedImage]) -> bytes:
        import httpx
        import requests
        from io import BytesIO
        from PIL import Image

        def image_data_url(image_bytes: bytes) -> str:
            with Image.open(BytesIO(image_bytes)) as image:
                image_format = (image.format or "PNG").lower()
            encoded = base64.b64encode(image_bytes).decode("utf-8")
            return f"data:image/{image_format};base64,{encoded}"

        def grok_image_response_bytes(response: object) -> bytes:
            image_bytes = getattr(response, "image", None)
            if isinstance(image_bytes, bytes):
                return image_bytes
            if isinstance(image_bytes, str):
                return base64.b64decode(image_bytes)

            image_url = getattr(response, "url", None)
            if isinstance(image_url, str):
                return httpx.get(image_url, timeout=120.0).content

            raise ValueError("Image generation returned no usable payload")

        def grok_http_error_message(exc: requests.HTTPError) -> str:
            response = exc.response
            if response is None:
                return "Grok nicht erreichbar - Verbindung pruefen."

            status = int(getattr(response, "status_code", 0) or 0)
            url = str(getattr(response, "url", "") or "")

            if status == 404 and "moderated_content.png" in url:
                return "Anfrage durch Moderation blockiert."
            if status == 429:
                return "Anfragelimit erreicht - bitte kurz warten."
            if status == 401:
                return "Authentifizierung fehlgeschlagen."
            if status >= 500:
                return f"Serverfehler ({status}) - bitte spaeter erneut versuchen."
            if status:
                return f"Fehler ({status})"
            return "Grok nicht erreichbar - Verbindung pruefen."

        image_urls = [image_data_url(image_bytes) for _name, image_bytes in images]

        payload: dict[str, object] = {
            "model": config.GROK_MODEL_LLM_IMG_BASE,
            "prompt": prompt,
            "resolution": "1k",
            "aspect_ratio": "9:16",
        }
        if len(image_urls) == 1:
            payload["image_url"] = image_urls[0]
        elif len(image_urls) > 1:
            payload["image_urls"] = image_urls

        try:
            response = self._sdk_client().image.sample(**payload)
            return grok_image_response_bytes(response)
        except requests.HTTPError as exc:
            raise RuntimeError(grok_http_error_message(exc)) from exc
        except requests.RequestException as exc:
            raise RuntimeError("Grok nicht erreichbar - Verbindung pruefen.") from exc

    def request_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._embed_texts(texts)


    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        embedding_fn = self._local_embedding_function()
        embeddings = embedding_fn(texts)
        return [list(vector) for vector in embeddings]

    def _local_embedding_function(self) -> Callable[..., list]:
        if self._local_embedding_fn is not None:
            return self._local_embedding_fn

        from fastembed import TextEmbedding
        from engine.storage import storage

        cache_dir = storage.etm_fastembed_cache
        cache_dir.mkdir(parents=True, exist_ok=True)

        model = TextEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_dir=str(cache_dir),
        )

        def fn(texts: list[str]) -> list[list[float]]:
            return [[float(value) for value in vector] for vector in model.embed(texts)]

        self._local_embedding_fn = fn
        return fn


    @staticmethod
    def _text_client() -> OpenAI:
        return OpenAI(api_key=config.GROK_API_KEY, base_url=config.GROK_BASE_URL)

    @staticmethod
    def _sdk_client() -> Any:
        from xai_sdk import Client
        return Client(api_key=config.GROK_API_KEY)



