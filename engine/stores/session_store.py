from __future__ import annotations

from typing import Any

from engine.config import config
from engine.models import Session
from engine.storage import npc_exists, scene_exists, storage

_ = config  # Re-export fuer Tests/Monkeypatching.

DEFAULT_NPC_ID = "vika"
DEFAULT_SCENE_ID = "office"


class SessionStore:
    @staticmethod
    def load() -> Session:
        data: dict[str, Any] = storage.session.get()
        npc_id = str(data.get("npc", DEFAULT_NPC_ID)).strip() or DEFAULT_NPC_ID
        scene_id = str(data.get("scene", DEFAULT_SCENE_ID)).strip() or DEFAULT_SCENE_ID

        return Session(npc_id=npc_id, scene_id=scene_id)

    def save(self, npc: str | None = None, scene: str | None = None) -> Session:
        if npc is not None and not npc_exists(npc):
            raise ValueError(f"NPC '{npc}' existiert nicht.")
        if scene is not None and not scene_exists(scene):
            raise ValueError(f"Scene '{scene}' existiert nicht.")

        current = self.load()
        updated = Session(
            npc_id=npc if npc is not None else current.npc_id,
            scene_id=scene if scene is not None else current.scene_id,
        )
        storage.session.save({"npc": updated.npc_id, "scene": updated.scene_id})
        return updated
