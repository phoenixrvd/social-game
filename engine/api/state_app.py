from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

from engine.api.models import SHORT_TEXT_MAX_LENGTH


RelativeUrl = Annotated[
    str,
    Field(
        pattern=r"^/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*$",
        max_length=2048,
        description="Relative URL innerhalb der Anwendung; muss mit '/' beginnen und darf keine externe Herkunft enthalten.",
    ),
]
EntityId = Annotated[
    str,
    Field(
        pattern=r"^[a-z0-9_]+$",
        max_length=SHORT_TEXT_MAX_LENGTH,
        description="Technische NPC- oder Szenen-ID aus Kleinbuchstaben, Ziffern und Unterstrichen.",
    ),
]


def url_version(path: Path) -> str:
    if not path.exists():
        return ""
    stat = path.stat()
    return f"{stat.st_mtime_ns}-{stat.st_size}"
