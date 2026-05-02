from __future__ import annotations

import math

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

    def distance_to(self, other: Episode) -> float:
        return 1.0 - self._cosine_similarity(other)

    def is_similar(self, other: Episode) -> bool:
        return self.distance_to(other) <= config.ETM_RETRIEVAL_MAX_DISTANCE

    def _cosine_similarity(self, other: Episode) -> float:
        dot_product = sum(left * right for left, right in zip(self.embedding, other.embedding, strict=False))
        norm_a = math.sqrt(sum(value * value for value in self.embedding))
        norm_b = math.sqrt(sum(value * value for value in other.embedding))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)


class SessionState(BaseModel):
    npc_id: str = Field(default_factory=lambda: config.DEFAULT_NPC_ID)
    scene_id: str = Field(default_factory=lambda: config.DEFAULT_SCENE_ID)

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


