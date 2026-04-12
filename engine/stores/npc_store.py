from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Iterable, Literal, cast
from uuid import uuid4

from engine.models import Npc, Scene, ShortMemoryMessage
from engine.storage import storage


class NpcStore:
    def _load_state(self) -> str:
        npc_paths = storage.npc
        runtime_state = npc_paths.state_runtime

        if runtime_state.is_file():
            return runtime_state.get()

        base_state = npc_paths.state_original.get().strip()
        relationship = npc_paths.relationship.get().strip()
        return "\n\n".join(part for part in (base_state, relationship) if part)

    def _load_scene(self) -> Scene:
        npc_paths = storage.npc
        scene_paths = storage.scene
        scene_img = scene_paths.img_original.get()
        runtime_scene = scene_paths.scene_runtime

        if runtime_scene.is_file():
            return Scene(scene_id=scene_paths.scene_id, description=runtime_scene.get(), img=scene_img)

        default = scene_paths.scene_original.get()

        npc_scene = npc_paths.scene_md_original
        if npc_scene.is_file():
            default = "\n".join([default, npc_scene.get()])

        return Scene(scene_id=scene_paths.scene_id, description=default, img=scene_img)

    def _load_stm(self) -> list[ShortMemoryMessage]:
        valid_roles = {"user", "assistant", "system"}
        rows = storage.npc.stm.get()

        return [
            ShortMemoryMessage(
                id=str(row.get("id", "")),
                timestamp_utc=str(row.get("timestamp_utc", "")),
                role=cast(Literal["user", "assistant", "system"], role),
                content=str(row.get("content", "")),
            )
            for row in rows
            if (role := row.get("role")) in valid_roles
        ]

    def load(self) -> Npc:
        npc_paths = storage.npc
        system_prompt = npc_paths.system_prompt_original.get()
        character = npc_paths.character_original.get()
        scene = self._load_scene()
        relationship = npc_paths.relationship.get()

        return Npc(
            npc_id=npc_paths.npc_id,
            description=npc_paths.description.get() or npc_paths.description_original.get(),
            system_prompt=system_prompt,
            character=character,
            state=self._load_state(),
            relationship=relationship,
            scene=scene,
            stm=self._load_stm(),
            img=storage.npc.img_original.get(),
            img_current=storage.npc.img_current.get(),
        )

    def append_stm(
        self,
        role: Literal["user", "assistant", "system"],
        content: str,
    ) -> ShortMemoryMessage:
        message = ShortMemoryMessage(
            id=str(uuid4()),
            timestamp_utc=datetime.now(UTC).isoformat(),
            role=role,
            content=content,
        )
        storage.npc.stm.append(asdict(message))
        return message

    def append_stm_turn(
        self,
        user_content: str,
        assistant_content: str,
    ) -> list[ShortMemoryMessage]:
        user_msg = self.append_stm("user", user_content)
        assistant_msg = self.append_stm("assistant", assistant_content)
        return [user_msg, assistant_msg]

    def remove_stm_by_ids(self, message_ids: Iterable[str]) -> None:
        remove_set = set(message_ids)
        if not remove_set:
            return

        current = self._load_stm()
        kept = [asdict(msg) for msg in current if msg.id not in remove_set]
        storage.npc.stm.save(kept)
