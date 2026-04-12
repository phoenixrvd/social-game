from __future__ import annotations

from engine.models import ShortMemoryMessage


def format_short_memory(messages: list[ShortMemoryMessage], last_n: int | None = None) -> str:
    if not messages:
        return "(keine Nachrichten)"

    selected = messages[-last_n:] if last_n is not None else messages
    return "\n".join(f"{message.role}: {message.content.strip()}" for message in selected)


def format_update_memory(messages: list[ShortMemoryMessage], last_n: int | None = None) -> str:
    if not messages:
        return "(keine Nachrichten)"

    role_labels = {"user": "U", "assistant": "A", "system": "S"}
    selected = messages[-last_n:] if last_n is not None else messages
    return "\n".join(f"{role_labels[message.role]}: {message.content.strip()}" for message in selected)
