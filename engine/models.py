from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal


@dataclass
class ChatMessage:
    role: str  # "player" oder "npc"
    content: str


@dataclass
class ShortMemoryMessage:
    id: str
    timestamp_utc: str
    role: Literal["user", "assistant", "system"]
    content: str


@dataclass
class Npc:
    npc_id: str
    description: str
    system_prompt: str
    state: str
    ltm: str
    scene: Scene
    img: Path = field(default_factory=Path)
    img_current: Path = field(default_factory=Path)
    stm: list[ShortMemoryMessage] = field(default_factory=list)
    character: dict[str, Any] = field(default_factory=dict)

    def has_messages_after(self, threshold: datetime) -> bool:
        return any(
            datetime.fromisoformat(message.timestamp_utc) > threshold 
            for message in self.stm
        )


@dataclass
class Scene:
    scene_id: str
    description: str
    img: Path = field(default_factory=Path)


@dataclass
class Session:
    npc_id: str
    scene_id: str


