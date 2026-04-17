from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from engine.config import config


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


class Stm(list[ShortMemoryMessage]):
    _ROLE_LABELS: dict[str, str] = {"user": "U", "assistant": "A", "system": "S"}

    def get_batch(self) -> Stm:
        messages_to_keep = config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP
        batch_size_threshold = config.UPDATER_ETM_BATCH_SIZE_THRESHOLD

        batch = Stm(self[:-messages_to_keep]) if messages_to_keep > 0 else Stm(self)
        if len(batch) <= batch_size_threshold:
            return Stm()
        return batch

    def as_string_short(self, last_n: int | None = None) -> str:
        selected = self[-last_n:] if last_n is not None else list(self)
        if not selected:
            return "(keine Nachrichten)"
        return "\n".join(f"{m.role}: {m.content.strip()}" for m in selected)

    def as_string_long(self, last_n: int | None = None) -> str:
        selected = self[-last_n:] if last_n is not None else list(self)
        if not selected:
            return "(keine Nachrichten)"
        return "\n".join(f"{self._ROLE_LABELS[m.role]}: {m.content.strip()}" for m in selected)


@dataclass
class Scene:
    scene_id: str
    description: str
    img: Path = field(default_factory=Path)


@dataclass
class Npc:
    npc_id: str
    description: str
    system_prompt: str
    state: str
    relationship: str
    scene: Scene
    img: Path = field(default_factory=Path)
    img_current: Path = field(default_factory=Path)
    stm: Stm = field(default_factory=Stm)
    character: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.stm, Stm):
            self.stm = Stm(self.stm)

    def has_messages_after(self, threshold: datetime) -> bool:
        return any(
            datetime.fromisoformat(message.timestamp_utc) > threshold
            for message in self.stm
        )


@dataclass
class Session:
    npc_id: str
    scene_id: str
