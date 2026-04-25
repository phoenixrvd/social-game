from __future__ import annotations

import base64
import re
from io import BytesIO
from typing import Any, Iterator

import httpx
import openai
import requests
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from PIL import Image

from engine.config import config
from engine.llm.provider_client import NamedImage, ProviderClient


class GrokProviderClient(ProviderClient):
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
        image_urls = [self._image_data_url(image_bytes) for _name, image_bytes in images]
        payload = self._image_payload(prompt, image_urls)

        try:
            response = self._sdk_client().image.sample(**payload)
            return self._image_response_bytes(response)
        except requests.HTTPError as exc:
            raise RuntimeError(self._http_error_message(exc)) from exc
        except requests.RequestException as exc:
            raise RuntimeError("Grok nicht erreichbar - Verbindung pruefen.") from exc

    @staticmethod
    def _llm_error_message(exc: openai.OpenAIError, provider_name: str) -> str:
        detail = GrokProviderClient._grok_user_visible_error_detail(str(exc))
        if detail is not None:
            return detail
        return ProviderClient._llm_error_message(exc, provider_name)

    @staticmethod
    def _image_data_url(image_bytes: bytes) -> str:
        with Image.open(BytesIO(image_bytes)) as image:
            image_format = (image.format or "PNG").lower()
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/{image_format};base64,{encoded}"

    @staticmethod
    def _image_response_bytes(response: object) -> bytes:
        try:
            image_bytes = getattr(response, "image", None)
        except ValueError:
            image_bytes = None
        if isinstance(image_bytes, bytes):
            return image_bytes
        if isinstance(image_bytes, str):
            return base64.b64decode(image_bytes)

        image_url = getattr(response, "url", None)
        if isinstance(image_url, str):
            return httpx.get(image_url, timeout=120.0).content

        raise ValueError("Image generation returned no usable payload")

    @staticmethod
    def _image_payload(prompt: str, image_urls: list[str]) -> dict[str, object]:
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
        return payload

    @staticmethod
    def _http_error_message(exc: requests.HTTPError) -> str:
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

    @staticmethod
    def _grok_user_visible_error_detail(text: str) -> str | None:
        if "grpc_message" not in text and "grpc_status" not in text:
            return None
        grpc_message = GrokProviderClient._grpc_message_text(text)
        source = grpc_message if grpc_message is not None else text
        if GrokProviderClient._is_quota_exhausted_message(source):
            return GrokProviderClient._trim_grok_message(source)
        return None

    @staticmethod
    def _grpc_message_text(text: str) -> str | None:
        match = re.search(r'grpc_message:(?:\\")?"?([^"}]+)"?', text)
        if match is None:
            return None
        return match.group(1).strip()

    @staticmethod
    def _is_quota_exhausted_message(text: str) -> bool:
        lower_text = text.lower()
        return (
            "used all available credits" in lower_text
            or "monthly spending limit" in lower_text
        )

    @staticmethod
    def _trim_grok_message(text: str) -> str:
        cleaned = text.strip()
        markers = (" Team:", " API key ID:", " Model:", " Failed check:", " Request ID:")
        for marker in markers:
            cut_index = cleaned.find(marker)
            if cut_index > 0:
                cleaned = cleaned[:cut_index].rstrip()
        return cleaned

    @staticmethod
    def _text_client() -> OpenAI:
        return OpenAI(api_key=config.GROK_API_KEY, base_url=config.GROK_BASE_URL)

    @staticmethod
    def _sdk_client() -> Any:
        from xai_sdk import Client
        return Client(api_key=config.GROK_API_KEY)



