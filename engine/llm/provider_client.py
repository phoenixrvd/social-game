from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable, Iterator, TypeVar

import ast
import json

import openai
import requests
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

NamedImage = tuple[str, bytes]
T = TypeVar("T")


# --- Text-Parse-Helfer ---

def _extract_object_segment(text: str) -> str | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return text[index : index + end]

    # Fallback fuer Provider-Texte mit Python-Dict-Snippets (single quotes).
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        return None
    return text[start : end + 1]


def _parse_object_segment(payload_text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(payload_text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    try:
        parsed = ast.literal_eval(payload_text)
        return parsed if isinstance(parsed, dict) else None
    except (ValueError, SyntaxError):
        return None


def _pick_error_message(payload: dict[str, Any]) -> str | None:
    for key in ("error", "message", "detail"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = _pick_error_message(value)
            if nested is not None:
                return nested
    return None


def _parsed_error_message(text: str) -> str | None:
    payload_text = _extract_object_segment(text)
    if payload_text is None:
        return None
    payload = _parse_object_segment(payload_text)
    if payload is None:
        return None
    return _pick_error_message(payload)


def _main_error_message(detail: str) -> str:
    cleaned = detail.strip()
    markers = (" Team:", " API key ID:", " Model:", " Failed check:", " Request ID:")
    for marker in markers:
        cut_index = cleaned.find(marker)
        if cut_index > 0:
            cleaned = cleaned[:cut_index].rstrip()
    return cleaned


# --- Fehler-Normalisierung (oeffentlich) ---

def normalize_provider_error_detail(text: str) -> str:
    detail = _parsed_error_message(text)
    source_text = detail if detail is not None else text
    return _main_error_message(source_text)


def _find_provider_error(exc: Exception) -> Exception | None:
    current: BaseException | None = exc
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if isinstance(current, Exception) and isinstance(
            current, (openai.OpenAIError, requests.RequestException)
        ):
            return current
        current = current.__cause__ or current.__context__
    return None


def _provider_error_texts(exc: Exception, provider_exc: Exception) -> list[str]:
    texts: list[str] = []
    for current in (exc, provider_exc):
        text = str(current).strip()
        if not text or text in texts:
            continue
        texts.append(text)
    return texts


def user_visible_provider_error_detail(exc: Exception) -> str | None:
    provider_exc = _find_provider_error(exc)
    if provider_exc is None:
        return None
    for text in _provider_error_texts(exc, provider_exc):
        detail = normalize_provider_error_detail(text)
        if detail:
            return detail
    return None


class ProviderClient(ABC):
    @abstractmethod
    def request_big(self, messages: list[ChatCompletionMessageParam]) -> Iterator[str]:
        raise NotImplementedError

    @abstractmethod
    def request_small(self, messages: list[ChatCompletionMessageParam]) -> str:
        raise NotImplementedError

    @abstractmethod
    def request_image(self, prompt: str, images: list[NamedImage]) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def request_embeddings(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @property
    @abstractmethod
    def _provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _text_client(self) -> OpenAI:
        raise NotImplementedError

    def _chat_request(self, model: str, messages: list[ChatCompletionMessageParam]) -> Iterator[str]:
        payload: dict[str, object] = {
            "model": model,
            "store": False,
            "messages": messages,
            "stream": True,
        }
        response = self._request(lambda client: client.chat.completions.create(**payload))
        return self._stream_chunks(response)

    def _request(self, action: Callable[[OpenAI], T]) -> T:
        try:
            return action(self._text_client())
        except openai.OpenAIError as exc:
            raise RuntimeError(self._llm_error_message(exc, self._provider_name)) from exc

    def _stream_chunks(self, stream: Iterable[object]) -> Iterator[str]:
        try:
            for chunk in stream:
                delta = self._extract_delta(chunk)
                if delta is None:
                    continue
                content = self._extract_delta_content(delta)
                if content is not None:
                    yield content
        except openai.OpenAIError as exc:
            raise RuntimeError(self._llm_error_message(exc, self._provider_name)) from exc

    # --- Fehler-Mapping (Provider-intern) ---

    @staticmethod
    def _llm_error_message(exc: openai.OpenAIError, provider_name: str) -> str:
        if isinstance(exc, openai.APIStatusError):
            code: str = getattr(exc, "code", None) or ""
            status = exc.status_code
            detail = ProviderClient._status_error_message(status, code)
            if detail is not None:
                return detail
            return normalize_provider_error_detail(str(exc)) or f"Fehler ({status})"
        if isinstance(exc, openai.APITimeoutError):
            return "Anfrage hat zu lange gedauert (Timeout)."
        if isinstance(exc, openai.APIConnectionError):
            return f"{provider_name} nicht erreichbar - Verbindung pruefen."
        return normalize_provider_error_detail(str(exc))

    @staticmethod
    def _status_error_message(status: int, code: str) -> str | None:
        error_codes: dict[str, str] = {
            "insufficient_quota": "Kontingent erschoepft - Plan und Abrechnung pruefen.",
            "rate_limit_exceeded": "Anfragelimit erreicht - bitte kurz warten.",
            "invalid_api_key": "Ungueltiger API-Schluessel.",
            "model_not_found": "Das angeforderte Modell wurde nicht gefunden.",
            "content_policy_violation": "Anfrage durch Inhaltsrichtlinien abgelehnt.",
            "moderation_blocked": "Anfrage durch Moderation blockiert.",
        }
        if code in error_codes:
            return error_codes[code]
        if status == 429:
            return "Anfragelimit erreicht - bitte kurz warten."
        if status == 401:
            return "Authentifizierung fehlgeschlagen."
        if status >= 500:
            return f"Serverfehler ({status}) - bitte spaeter erneut versuchen."
        return None

    # --- Delta-Extraktion ---

    @staticmethod
    def _extract_delta(chunk: object) -> Any | None:
        choices = getattr(chunk, "choices", None)
        if not choices:
            return None
        return getattr(choices[0], "delta", None)

    @staticmethod
    def _extract_delta_content(delta: Any) -> str | None:
        content = getattr(delta, "content", None)
        return content if isinstance(content, str) and content else None
