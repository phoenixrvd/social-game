from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, field_validator, Field

from engine.config import config


class Message(BaseModel):
    id: str
    timestamp_utc: str
    role: Literal["user", "assistant", "system"]
    content: str
    model_config = {"str_strip_whitespace": True}

    @property
    def text_short(self) -> str:
        role_labels = {"user": "U", "assistant": "A", "system": "S"}
        return f"{role_labels[self.role]}: {self.content.strip()}"

    @property
    def text_long(self) -> str:
        return f"{self.role}: {self.content.strip()}"


class Episode(BaseModel):
    id: str
    text: str
    embedding: list[float]
    created_at: str


class SessionState(BaseModel):
    npc_id: str = Field(default_factory=lambda: config.DEFAULT_NPC_ID)
    scene_id: str = Field(default_factory=lambda: config.DEFAULT_SCENE_ID)
    image_autogenerate: bool = True

    @field_validator("npc_id")
    @classmethod
    def validate_npc(cls, value: str) -> str:
        from engine.storage.paths import path_resolver
        if not path_resolver.npc_exists(value):
            raise ValueError(f"NPC '{value}' existiert nicht.")
        return value

    @field_validator("scene_id")
    @classmethod
    def validate_scene(cls, value: str) -> str:
        from engine.storage.paths import path_resolver
        if not path_resolver.scene_exists(value):
            raise ValueError(f"Scene '{value}' existiert nicht.")
        return value

