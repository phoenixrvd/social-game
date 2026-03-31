from __future__ import annotations

from typing import Any

from engine.config import config
from engine.models import Session
from engine.fs_utils import load_yaml, save_yaml

DEFAULT_NPC_ID = "vika"
DEFAULT_SCENE_ID = "office"


class SessionStore:
    def load(self) -> Session:
        data: dict[str, Any] = load_yaml(config.SESSION_PATH)
        npc_id = str(data.get("npc", DEFAULT_NPC_ID)).strip() or DEFAULT_NPC_ID
        scene_id = str(data.get("scene", DEFAULT_SCENE_ID)).strip() or DEFAULT_SCENE_ID

        return Session(npc_id=npc_id, scene_id=scene_id)

    def save(self, *, npc: str | None = None, scene: str | None = None) -> Session:
        if npc is not None and not (config.NPC_DIR / npc).is_dir():
            raise ValueError(f"NPC '{npc}' existiert nicht.")
        if scene is not None and not (config.SCENE_DIR / scene).is_dir():
            raise ValueError(f"Scene '{scene}' existiert nicht.")

        current = self.load()
        updated = Session(
            npc_id=npc if npc is not None else current.npc_id,
            scene_id=scene if scene is not None else current.scene_id,
        )
        save_yaml(config.SESSION_PATH, {"npc": updated.npc_id, "scene": updated.scene_id})
        return updated

