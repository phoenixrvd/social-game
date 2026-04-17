from __future__ import annotations

import base64
from typing import Callable, Iterable, Iterator

import httpx
import openai
import requests
from fastembed import TextEmbedding
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from PIL import Image
from io import BytesIO

from engine.config import config
from engine.llm.client_interface import ClientInterface, NamedImage
from engine.llm.error_utils import llm_error_message
from engine.storage import storage


def _image_data_url(image_bytes: bytes) -> str:
    with Image.open(BytesIO(image_bytes)) as image:
        image_format = (image.format or "PNG").lower()
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/{image_format};base64,{encoded}"


def _grok_image_response_bytes(response: object) -> bytes:
    image_bytes = getattr(response, "image", None)
    if isinstance(image_bytes, bytes):
        return image_bytes
    if isinstance(image_bytes, str):
        return base64.b64decode(image_bytes)
    image_url = getattr(response, "url", None)
    if isinstance(image_url, str):
        return httpx.get(image_url, timeout=120.0).content
    raise ValueError("Image generation returned no usable payload")


def _grok_http_error_message(exc: requests.HTTPError) -> str:
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


class ClientGrok(ClientInterface):
    def __init__(self) -> None:
        self._local_embedding_fn: Callable[..., list] | None = None

    def big_request(
        self,
        messages: list[ChatCompletionMessageParam],
        *,
        stream: bool,
    ) -> str | Iterator[str]:
        try:
            response = self._text_client().chat.completions.create(
                model=config.GROK_MODEL_LLM_BIG, store=False, messages=messages, stream=stream,
            )
            if not stream:
                return response.choices[0].message.content or ""
            return self._stream_chunks(response, provider_name="Grok")
        except openai.OpenAIError as exc:
            raise RuntimeError(llm_error_message(exc, "Grok")) from exc

    def small_request(
        self,
        messages: list[ChatCompletionMessageParam],
    ) -> str:
        try:
            response = self._text_client().chat.completions.create(
                model=config.GROK_MODEL_LLM_SMALL, store=False, messages=messages, stream=False,
            )
            return response.choices[0].message.content or ""
        except openai.OpenAIError as exc:
            raise RuntimeError(llm_error_message(exc, "Grok")) from exc

    def image_request(self, prompt: str, images: list[NamedImage]) -> bytes:
        image_urls = [_image_data_url(image_bytes) for _name, image_bytes in images]
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
            return _grok_image_response_bytes(response)
        except requests.HTTPError as exc:
            raise RuntimeError(_grok_http_error_message(exc)) from exc
        except requests.RequestException as exc:
            raise RuntimeError("Grok nicht erreichbar - Verbindung pruefen.") from exc

    def embedding_request(self, texts: list[str]) -> list[list[float]]:
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
        cache_dir = storage.etm_fastembed_cache
        cache_dir.mkdir(parents=True, exist_ok=True)
        model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2", cache_dir=str(cache_dir))

        def fn(texts: list[str]) -> list[list[float]]:
            return [[float(value) for value in vector] for vector in model.embed(texts)]

        self._local_embedding_fn = fn
        return fn

    @staticmethod
    def _text_client() -> OpenAI:
        return OpenAI(api_key=config.GROK_API_KEY, base_url=config.GROK_BASE_URL)

    @staticmethod
    def _sdk_client():
        from xai_sdk import Client

        return Client(api_key=config.GROK_API_KEY)

    @staticmethod
    def _stream_chunks(stream: Iterable[object], *, provider_name: str) -> Iterator[str]:
        try:
            for chunk in stream:
                choices = getattr(chunk, "choices", None)
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                content = getattr(delta, "content", None)
                if isinstance(content, str) and content:
                    yield content
        except openai.OpenAIError as exc:
            raise RuntimeError(llm_error_message(exc, provider_name)) from exc
