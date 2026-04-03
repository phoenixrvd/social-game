import base64
from io import BytesIO
from typing import Iterator, TypeVar, cast

import openai
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam, ChatCompletionStreamOptionsParam
from pydantic import BaseModel

from engine.logging import get_logger, log_info
from engine.config import config

TStructured = TypeVar("TStructured", bound=BaseModel)
LOGGER = get_logger("llm_client")

_OPENAI_ERROR_CODES: dict[str, str] = {
    "insufficient_quota": "Kontingent erschöpft – Plan und Abrechnung prüfen.",
    "rate_limit_exceeded": "Anfragelimit erreicht – bitte kurz warten.",
    "invalid_api_key": "Ungültiger API-Schlüssel.",
    "model_not_found": "Das angeforderte Modell wurde nicht gefunden.",
    "content_policy_violation": "Anfrage durch Inhaltsrichtlinien abgelehnt.",
    "moderation_blocked": "Anfrage durch Moderation blockiert.",
}


def _openai_error_message(exc: openai.OpenAIError) -> str:
    if isinstance(exc, openai.APIStatusError):
        code: str = getattr(exc, "code", None) or ""
        status: int = exc.status_code
        if code in _OPENAI_ERROR_CODES:
            return _OPENAI_ERROR_CODES[code]
        if status == 429:
            return "Anfragelimit erreicht – bitte kurz warten."
        if status == 401:
            return "Authentifizierung fehlgeschlagen."
        if status >= 500:
            return f"Serverfehler ({status}) – bitte später erneut versuchen."
        return f"Fehler ({status})"
    if isinstance(exc, openai.APIConnectionError):
        return "OpenAI nicht erreichbar – Verbindung prüfen."
    if isinstance(exc, openai.APITimeoutError):
        return "Anfrage hat zu lange gedauert (Timeout)."
    return str(exc)


def hello_llm():
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    response1 = client.responses.create(
        model=config.MODEL_LLM_SMALL,
        input=f"Antworte nur mit: Hallo aus dem SML ({config.MODEL_LLM_SMALL})",
    )

    response2 = client.responses.create(
        model=config.MODEL_LLM_BIG,
        input=f"Antworte nur mit: Hallo aus dem LLM ({config.MODEL_LLM_BIG})",
    )

    return "\n".join([
        response1.output_text,
        response2.output_text
    ])


def stream_prompt(messages: list[ChatCompletionMessageParam]) -> Iterator[str]:
    """Streamt die NPC-Antwort tokenweise/chunkweise."""
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    stream_options: ChatCompletionStreamOptionsParam = {
        "include_usage": True,
    }

    try:
        stream = client.chat.completions.create(
            model=config.MODEL_LLM_BIG,
            store=False,
            messages=messages,
            stream=True,
            stream_options=stream_options
        )

        usage = None

        for chunk in stream:
            chunk_usage = getattr(chunk, "usage", None)
            if chunk_usage is not None:
                usage = chunk_usage

            if not chunk.choices:
                continue
            delta_text = chunk.choices[0].delta.content
            if delta_text:
                yield delta_text

        if usage is None:
            log_info(LOGGER, "chat_tokens", unavailable=True, message_count=len(messages))
            return

        prompt_tokens_details = getattr(usage, "prompt_tokens_details", None)
        cached_tokens = 0 if prompt_tokens_details is None else getattr(prompt_tokens_details, "cached_tokens", 0) or 0
        log_info(LOGGER, "chat_tokens", prompt_tokens=usage.prompt_tokens, completion_tokens=usage.completion_tokens, total_tokens=usage.total_tokens, cached_tokens=cached_tokens, unavailable=False, message_count=len(messages))
    except openai.OpenAIError as exc:
        raise RuntimeError(_openai_error_message(exc)) from exc


def run_prompt(prompt: str, model: str = config.MODEL_LLM_BIG) -> str:
    """Fuehrt einen einfachen User-Prompt aus und gibt den Textinhalt der ersten Antwort zurueck."""
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model=model,
            store=False,
            messages=[cast(
                ChatCompletionUserMessageParam,
                cast(object, {"role": "user", "content": prompt}),
            )],
        )
        return response.choices[0].message.content or ""
    except openai.OpenAIError as exc:
        raise RuntimeError(_openai_error_message(exc)) from exc


def refresh_img(prompt: str, reference_img_bytes: bytes) -> bytes:
    """Erzeugt ein neues PNG auf Basis eines Referenzbildes."""
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    image_file = BytesIO(reference_img_bytes)
    image_file.name = "img.png"

    try:
        result = client.images.edit(
            model=config.MODEL_LLM_IMG_BASE,
            image=image_file,
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
        raise RuntimeError(_openai_error_message(exc)) from exc

    if not result.data:
        raise ValueError("Image generation returned no data")

    b64_data = result.data[0].b64_json
    if not b64_data:
        raise ValueError("Image generation returned no base64 payload")

    return base64.b64decode(b64_data)
