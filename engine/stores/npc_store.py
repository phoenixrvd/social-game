from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Literal
from uuid import uuid4

from engine.config import config
from engine.models import Npc, Scene, ShortMemoryMessage
from engine.fs_utils import load_text, load_yaml, save_text, append_jsonl, load_jsonl, save_jsonl
from engine.stores.session_store import SessionStore


class NpcStore:
    def __init__(self) -> None:
        self.session_store = SessionStore()

    def _npc_scene_data_dir(self, npc_id: str, scene_id: str) -> Path:
        return config.DATA_NPC_DIR / npc_id / scene_id

    def _runtime_path(self, npc_id: str, scene_id: str, filename: str) -> Path:
        return self._npc_scene_data_dir(npc_id, scene_id) / filename

    def _load_scene(self, npc_id: str, scene_id: str) -> Scene:
        session = self._runtime_path(npc_id, scene_id, "scene.md")

        if session.is_file():
            return Scene(scene_id=scene_id, description=load_text(session))

        default = load_text(config.SCENE_DIR / scene_id / "scene.md")

        scene = config.NPC_DIR / npc_id / "scenes" / scene_id / "scene.md"
        if scene.is_file():
            default =  "\n".join([default, load_text(scene)])

        return Scene(scene_id=scene_id, description=default)

    def _load_default_files(self, npc_id: str) -> dict[str, Any]:
        npc_dir = config.NPC_DIR / npc_id
        return {
            "description": load_text(npc_dir / "description.md"),
            "system_prompt": load_text(npc_dir / "system_prompt.md"),
            "character": load_yaml(npc_dir / "character.yaml"),
            "state": load_text(npc_dir / "state.md"),
            "ltm": load_text(npc_dir / "ltm.md"),
        }

    def _load_runtime_value(self, npc_id: str, scene_id: str, filename: str, default: str) -> str:
        value = load_text(self._runtime_path(npc_id, scene_id, filename))
        return value if value else default

    def _stm_path(self, npc_id: str, scene_id: str) -> Path:
        return self._runtime_path(npc_id, scene_id, "stm.jsonl")

    def _load_current_image_path(self, npc_id: str, scene_id: str) -> Path:
        session = self._runtime_path(npc_id, scene_id, "img.png")
        if session.is_file():
            return session

        scene = config.NPC_DIR / npc_id / "scenes" / scene_id / "img.png"
        if scene.is_file():
            return scene

        return  config.NPC_DIR / npc_id / "img.png"

    def _load_stm(self, npc_id: str, scene_id: str) -> list[ShortMemoryMessage]:
        valid_roles = {"user", "assistant", "system"}
        rows = load_jsonl(self._stm_path(npc_id, scene_id))

        return [
            ShortMemoryMessage(
                id=str(row.get("id", "")),
                timestamp_utc=str(row.get("timestamp_utc", "")),
                role=role,
                content=str(row.get("content", "")),
            )
            for row in rows
            if (role := row.get("role")) in valid_roles
        ]

    def load(self) -> Npc:
        session = self.session_store.load()
        resolved_npc_id = session.npc_id
        resolved_scene_id = session.scene_id

        raw = self._load_default_files(resolved_npc_id)
        scene = self._load_scene(resolved_npc_id, resolved_scene_id)

        return Npc(
            npc_id=resolved_npc_id,
            description=raw["description"],
            system_prompt=raw["system_prompt"],
            character=raw["character"],
            state=self._load_runtime_value(resolved_npc_id, resolved_scene_id, "state.md", raw["state"]),
            ltm=self._load_runtime_value(resolved_npc_id, resolved_scene_id, "ltm.md", raw["ltm"]),
            scene=scene,
            stm=self._load_stm(resolved_npc_id, resolved_scene_id),
            img=self._load_current_image_path(resolved_npc_id, resolved_scene_id),
        )

    def save_state(self, npc_id: str, scene_id: str, state: str) -> None:
        save_text(self._runtime_path(npc_id, scene_id, "state.md"), state)

    def save_ltm(self, npc_id: str, scene_id: str, ltm: str) -> None:
        save_text(self._runtime_path(npc_id, scene_id, "ltm.md"), ltm)

    def save_scene(self, npc_id: str, scene_id: str, scene: str) -> None:
        save_text(self._runtime_path(npc_id, scene_id, "scene.md"), scene)

    def append_stm(
        self,
        npc_id: str,
        scene_id: str,
        role: Literal["user", "assistant", "system"],
        content: str,
    ) -> ShortMemoryMessage:
        message = ShortMemoryMessage(
            id=str(uuid4()),
            timestamp_utc=datetime.now(UTC).isoformat(),
            role=role,
            content=content,
        )
        append_jsonl(self._stm_path(npc_id, scene_id), asdict(message))
        return message

    def append_stm_turn(
        self,
        user_content: str,
        assistant_content: str,
    ) -> list[ShortMemoryMessage]:
        session = self.session_store.load()
        npc_id = session.npc_id
        scene_id = session.scene_id
        user_msg = self.append_stm(npc_id, scene_id, "user", user_content)
        assistant_msg = self.append_stm(npc_id, scene_id, "assistant", assistant_content)
        return [user_msg, assistant_msg]

    def remove_stm_by_ids(self, npc_id: str, scene_id: str, message_ids: Iterable[str]) -> None:
        remove_set = set(message_ids)
        if not remove_set:
            return

        current = self._load_stm(npc_id, scene_id)
        kept = [asdict(msg) for msg in current if msg.id not in remove_set]
        save_jsonl(self._stm_path(npc_id, scene_id), kept)
