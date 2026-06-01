from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import Field

from engine.api.models import ApiModel, CHAT_MESSAGE_MAX_LENGTH
from engine.client import client, user_visible_provider_error_detail
from engine.services.npc_turn_service import NpcTurnService
from engine.tools.scheduler import get_scheduler

router = APIRouter(tags=["chat"])


class ChatRequest(ApiModel):
    message: str = Field(
        min_length=1,
        max_length=CHAT_MESSAGE_MAX_LENGTH,
        pattern=r".*\S.*",
        description="Nicht leere Nutzer-Nachricht, die an den aktiven NPC gesendet wird.",
    )


class ChatStreamEvent(ApiModel):
    type: str = Field(description="Event-Typ im NDJSON-Stream: 'chunk', 'done' oder 'error'.")
    delta: str | None = Field(default=None, description="Textfragment der NPC-Antwort; nur bei 'chunk' gesetzt.")
    detail: str | None = Field(default=None, description="Nutzerlesbare Fehlermeldung; nur bei 'error' gesetzt.")


def _stream_event(event_type: str, **payload: object) -> str:
    return json.dumps({"type": event_type, **payload}, ensure_ascii=False) + "\n"


def _stream_error_event(exc: Exception) -> str:
    detail = user_visible_provider_error_detail(exc) or "Interner Serverfehler."
    return _stream_event("error", detail=detail)


def _stream_events(
    npc_turn: NpcTurnService,
    message_text: str,
    prompt_stream: Iterator[str],
) -> Iterator[str]:
    parts: list[str] = []

    try:
        for part in prompt_stream:
            parts.append(part)
            yield _stream_event("chunk", delta=part)
    except Exception as exc:
        yield _stream_error_event(exc)
        return

    reply = "".join(parts).strip()

    try:
        npc_turn.finalize_turn(message_text, reply)
        get_scheduler().enqueue_all()
    except Exception as exc:
        yield _stream_error_event(exc)
        return

    yield _stream_event("done")


@router.post(
    "/api/chat/stream",
    summary="Chat streamen",
    responses={
        200: {
            "description": "NDJSON-Stream mit Chat-Events. Jede Zeile ist ein JSON-Objekt vom Typ `chunk`, `done` oder `error`.",
            "content": {
                "application/x-ndjson": {
                    "schema": ChatStreamEvent.model_json_schema(),
                }
            },
        },
    },
)
def stream(request: ChatRequest) -> StreamingResponse:
    """Sendet eine nicht leere Nutzer-Nachricht an den aktiven NPC und streamt die Antwort als NDJSON. Jede Zeile enthält ein Event vom Typ `chunk`, `done` oder `error`."""
    npc_turn = NpcTurnService()
    message_text = request.message.strip()

    try:
        prompt_stream = client.stream_prompt(npc_turn.build_chat_messages(message_text))
    except Exception as exc:
        return StreamingResponse(iter([_stream_error_event(exc)]), media_type="application/x-ndjson")

    return StreamingResponse(
        _stream_events(npc_turn, message_text, prompt_stream),
        media_type="application/x-ndjson",
    )
