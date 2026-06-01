import ast
import base64
import json
from io import BytesIO
from typing import Any, Callable, Iterable, Iterator, TypeVar, cast

import httpx
import openai
import requests
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from PIL import Image
from pydantic import BaseModel

from engine.config import config
from engine.logger import logger

NamedImage = tuple[str, bytes]
T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=BaseModel)


def _extract_provider_object_segment(text: str) -> str | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        parsed_segment = _decode_provider_object_segment(decoder, text, index)
        if parsed_segment is not None:
            return parsed_segment
    return _fallback_provider_object_segment(text)


def _decode_provider_object_segment(decoder: json.JSONDecoder, text: str, index: int) -> str | None:
    try:
        parsed, end = decoder.raw_decode(text[index:])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return text[index : index + end]


def _fallback_provider_object_segment(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        return None
    return text[start : end + 1]


def _parse_provider_object_segment(payload_text: str) -> dict[str, Any] | None:
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(payload_text)
        except (json.JSONDecodeError, ValueError, SyntaxError):
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _pick_provider_error_message(payload: dict[str, Any]) -> str | None:
    for key in ("error", "message", "detail"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested_message = _pick_provider_error_message(value)
            if nested_message is not None:
                return nested_message
    return None


def _parsed_provider_error_message(text: str) -> str | None:
    payload_text = _extract_provider_object_segment(text)
    if payload_text is None:
        return None
    payload = _parse_provider_object_segment(payload_text)
    if payload is None:
        return None
    return _pick_provider_error_message(payload)


def _main_provider_error_message(detail: str) -> str:
    cleaned = detail.strip()
    markers = (" Team:", " API key ID:", " Model:", " Failed check:", " Request ID:")
    for marker in markers:
        cut_index = cleaned.find(marker)
        if cut_index > 0:
            cleaned = cleaned[:cut_index].rstrip()
    return cleaned


class CompressedImage:
    def __init__(self, name: str, image_bytes: bytes) -> None:
        self.name = name
        self.image_bytes = image_bytes

    def compress(self, scale_factor: float = 0.9, quality: int = 88) -> NamedImage:
        with Image.open(BytesIO(self.image_bytes)) as image:
            normalized = image.convert("RGBA")
            resized = self._resize(normalized, scale_factor)
            flattened = self._flatten_alpha(resized)
            return self.name, self._encode_jpeg(flattened, quality)

    @staticmethod
    def _resize(image: Image.Image, scale_factor: float) -> Image.Image:
        width = max(1, round(image.width * scale_factor))
        height = max(1, round(image.height * scale_factor))
        if image.size == (width, height):
            return image
        return image.resize((width, height), Image.Resampling.LANCZOS)

    @staticmethod
    def _flatten_alpha(image: Image.Image) -> Image.Image:
        flattened = Image.new("RGB", image.size, (255, 255, 255))
        flattened.paste(image, mask=image.getchannel("A"))
        return flattened

    def _encode_jpeg(self, image: Image.Image, quality: int) -> bytes:
        compressed = BytesIO()
        compressed.name = self.name
        image.save(compressed, format="JPEG", quality=quality, optimize=True, progressive=True)
        return compressed.getvalue()


class Client:
    def stream_prompt(self, messages: list[ChatCompletionMessageParam]) -> Iterator[str]:
        yield from self._request_big(messages)

    def embed_texts(self, text: str) -> list[float]:
        cleaned = text.strip()
        if not cleaned:
            return []
        return self._request_embedding(cleaned)

    def run_prompt_small(self, prompt: str) -> str:
        cleaned = prompt.strip()
        if not cleaned:
            return ""
        user_message = cast(ChatCompletionMessageParam, cast(object, {"role": "user", "content": cleaned}))
        return self._request_small([user_message])

    def run_messages_small(self, messages: list[ChatCompletionMessageParam]) -> str:
        if not messages:
            return ""
        return self._request_small(messages)

    def run_prompt_small_model(self, prompt: str, response_model: type[ModelT]) -> ModelT:
        cleaned = prompt.strip()
        if not cleaned:
            raise ValueError("Modell-Prompt darf nicht leer sein.")
        user_message = cast(ChatCompletionMessageParam, cast(object, {"role": "user", "content": cleaned}))
        return self._request_small_model([user_message], response_model=response_model)

    def generate_scene_img(self, prompt: str) -> bytes:
        cleaned = prompt.strip()
        if not cleaned:
            raise ValueError("Bildprompt darf nicht leer sein.")
        return self._request_scene_image(cleaned)

    def generate_scene_img_from_reference(self, prompt: str, reference_img_bytes: bytes) -> bytes:
        cleaned = prompt.strip()
        if not cleaned:
            raise ValueError("Bildprompt darf nicht leer sein.")
        image = CompressedImage("scene-reference.jpg", reference_img_bytes).compress(scale_factor=1.0, quality=90)
        return self._request_image(cleaned, [image], input_fidelity="high")

    def generate_npc_img_from_reference(self, prompt: str, reference_img_bytes: bytes) -> bytes:
        cleaned = prompt.strip()
        if not cleaned:
            raise ValueError("Bildprompt darf nicht leer sein.")
        image = CompressedImage("npc-reference.jpg", reference_img_bytes).compress(scale_factor=1.0, quality=90)
        return self._request_image(cleaned, [image], input_fidelity="low")

    def describe_scene_reference_img(self, prompt: str, reference_img_bytes: bytes) -> str:
        cleaned = prompt.strip()
        if not cleaned:
            return ""
        image = CompressedImage("scene-reference.jpg", reference_img_bytes).compress(scale_factor=1.0, quality=90)
        return self._request_small([self._image_user_message(cleaned, image)])

    def describe_npc_reference_img(self, prompt: str, reference_img_bytes: bytes) -> str:
        cleaned = prompt.strip()
        if not cleaned:
            return ""
        image = CompressedImage("npc-reference.jpg", reference_img_bytes).compress(scale_factor=1.0, quality=90)
        return self._request_small([self._image_user_message(cleaned, image)])

    def refresh_img(self, prompt: str, reference_img_bytes: bytes, identity_img_bytes: bytes | None = None) -> bytes:
        images = [CompressedImage("current.jpg", reference_img_bytes).compress(scale_factor=0.8, quality=82)]
        if identity_img_bytes is not None:
            identity = CompressedImage("identity.jpg", identity_img_bytes).compress(scale_factor=1.0, quality=92)
            images = [identity, *images]
        return self._request_image(prompt, images)

    def merge_character_scene_img(self, prompt: str, character_img_bytes: bytes, scene_img_bytes: bytes) -> bytes:
        images = [
            CompressedImage("character.jpg", character_img_bytes).compress(),
            CompressedImage("scene.jpg", scene_img_bytes).compress(),
        ]
        return self._request_image(prompt, images)

    def _request_big(self, messages: list[ChatCompletionMessageParam]) -> Iterator[str]:
        return self._chat_request(config.MODEL_LLM_BIG, messages)

    def _request_small(self, messages: list[ChatCompletionMessageParam]) -> str:
        return "".join(self._chat_request(config.MODEL_LLM_SMALL, messages))

    def _request_small_model(self, messages: list[ChatCompletionMessageParam], *, response_model: type[ModelT]) -> ModelT:
        response = self._request(
            lambda openai_client: openai_client.beta.chat.completions.parse(
                model=config.MODEL_LLM_SMALL,
                store=False,
                messages=messages,
                response_format=response_model,
            )
        )
        return self._response_message_parsed(response, response_model)

    def _request_embedding(self, text: str) -> list[float]:
        response = self._request(
            lambda openai_client: openai_client.embeddings.create(
                model=config.MODEL_EMBEDDING,
                input=[text],
            )
        )
        embedding = response.data[0].embedding
        return [float(value) for value in embedding]

    def _request_image(self, prompt: str, images: list[NamedImage], input_fidelity: str = "low") -> bytes:
        payload = self._image_payload(images)
        image_arg: BytesIO | list[BytesIO] = payload[0] if len(payload) == 1 else payload
        result = self._request(
            lambda openai_client: openai_client.images.edit(
                model=config.MODEL_IMAGE,
                image=image_arg,
                prompt=prompt,
                n=1,
                size="1024x1536",
                quality="low",
                background="auto",
                input_fidelity=input_fidelity,
                extra_query={"moderation": "low"},
                extra_body={"moderation": "low"},
            )
        )
        return self._decode_image_result(result)

    def _request_scene_image(self, prompt: str) -> bytes:
        result = self._request(
            lambda openai_client: openai_client.images.generate(
                model=config.MODEL_IMAGE,
                prompt=prompt,
                n=1,
                size="1024x1536",
                quality="low",
                background="auto",
                moderation="low",
            )
        )
        return self._decode_image_result(result)

    @staticmethod
    def _decode_image_result(result: Any) -> bytes:
        encoded_image = result.data[0].b64_json
        if encoded_image is None:
            raise RuntimeError("OpenAI-Bildantwort enthaelt kein Bildpayload.")
        return base64.b64decode(encoded_image)

    @staticmethod
    def _image_payload(images: list[NamedImage]) -> list[BytesIO]:
        payload: list[BytesIO] = []
        for name, image_bytes in images:
            image_file = BytesIO(image_bytes)
            image_file.name = name
            payload.append(image_file)
        return payload

    @staticmethod
    def _image_user_message(prompt: str, image: NamedImage) -> ChatCompletionMessageParam:
        image_data = base64.b64encode(image[1]).decode("ascii")
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
        ]
        return cast(ChatCompletionMessageParam, cast(object, {"role": "user", "content": content}))

    def _chat_request(self, model: str, messages: list[ChatCompletionMessageParam]) -> Iterator[str]:
        payload: dict[str, object] = {"model": model, "store": False, "messages": messages, "stream": True}
        response = self._request(lambda openai_client: openai_client.chat.completions.create(**payload))
        return self._stream_chunks(response)

    @staticmethod
    def _response_message_parsed(response: Any, response_model: type[ModelT]) -> ModelT:
        choices = getattr(response, "choices", None)
        if not choices:
            raise RuntimeError("LLM-Antwort enthaelt keine Auswahl.")
        message = getattr(choices[0], "message", None)
        parsed = getattr(message, "parsed", None) if message is not None else None
        if isinstance(parsed, response_model):
            return parsed
        refusal = getattr(message, "refusal", "") if message is not None else ""
        if isinstance(refusal, str) and refusal.strip():
            raise RuntimeError(f"LLM-Antwort wurde abgelehnt: {refusal.strip()}")
        raise RuntimeError(f"LLM-Antwort enthaelt kein parsebares {response_model.__name__}-Objekt.")

    def _request(self, action: Callable[[OpenAI], T]) -> T:
        try:
            return action(self._text_client())
        except openai.OpenAIError as exc:
            error_msg = self._llm_error_message(exc)
            logger.error(f"LLM Request Error (Base URL: {config.MODEL_BASE_URL}): {type(exc).__name__} - {error_msg}")
            raise RuntimeError(error_msg) from exc

    def _stream_chunks(self, stream: Iterable[object]) -> Iterator[str]:
        try:
            for chunk in stream:
                content = self._chunk_content(chunk)
                if content is None:
                    continue
                yield content
        except openai.OpenAIError as exc:
            raise RuntimeError(self._llm_error_message(exc)) from exc

    def _chunk_content(self, chunk: object) -> str | None:
        delta = self._extract_delta(chunk)
        if delta is None:
            return None
        return self._extract_delta_content(delta)

    def _llm_error_message(self, exc: openai.OpenAIError) -> str:
        if isinstance(exc, openai.APIStatusError):
            return self._api_status_error_message(exc)
        if isinstance(exc, openai.APITimeoutError):
            return "Anfrage hat zu lange gedauert (Timeout)."
        if isinstance(exc, openai.APIConnectionError):
            return self._api_connection_error_message(exc)
        return normalize_provider_error_detail(str(exc))

    def _api_status_error_message(self, exc: openai.APIStatusError) -> str:
        code: str = getattr(exc, "code", None) or ""
        detail = self._status_error_message(exc.status_code, code)
        if detail is not None:
            return detail
        normalized = normalize_provider_error_detail(str(exc))
        return normalized or f"Fehler ({exc.status_code})"

    def _api_connection_error_message(self, exc: openai.APIConnectionError) -> str:
        error_text = str(exc).strip()
        base_url = config.MODEL_BASE_URL
        if self._is_ssl_certificate_error(error_text):
            ssl_hint = " [Tipp: SG_MODEL_VERIFY_SSL=false in .env für selbstsignierte Zertifikate]"
            return f"SSL-Zertifikatsfehler zu {base_url}{ssl_hint}"

        original_error = getattr(exc, "__cause__", None)
        cause_msg = f" ({type(original_error).__name__})" if original_error else ""
        if error_text:
            return f"Verbindungsfehler zu {base_url}{cause_msg}: {error_text}"
        return f"Verbindungsfehler zu {base_url}{cause_msg} - konfiguration oder netzwerk pruefen."

    @staticmethod
    def _is_ssl_certificate_error(error_text: str) -> bool:
        return "CERTIFICATE_VERIFY_FAILED" in error_text or "SSL" in error_text

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

    @staticmethod
    def _text_client() -> OpenAI:
        http_client = httpx.Client(verify=config.MODEL_VERIFY_SSL, timeout=config.MODEL_TIMEOUT_SECONDS)
        return OpenAI(
            api_key=config.MODEL_API_KEY,
            base_url=config.MODEL_BASE_URL,
            http_client=http_client,
            timeout=config.MODEL_TIMEOUT_SECONDS,
        )


def normalize_provider_error_detail(text: str) -> str:
    detail = _parsed_provider_error_message(text)
    source_text = detail if detail is not None else text
    return _main_provider_error_message(source_text)


def _find_provider_error(exc: Exception) -> Exception | None:
    current: BaseException | None = exc
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        is_provider_error = isinstance(current, (openai.OpenAIError, requests.RequestException))
        if isinstance(current, Exception) and is_provider_error:
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


client = Client()
