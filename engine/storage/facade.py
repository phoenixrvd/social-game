from __future__ import annotations

from pathlib import Path

from engine.config import config
from engine.storage.nodes import NpcNode, PromptsNode, SceneNode, SessionNode
from engine.storage.paths import path_resolver


class Storage:
    def npc_view(self, npc_id: str, scene_id: str = "") -> NpcNode:
        return NpcNode(npc_id=npc_id, scene_id=scene_id)

    def scene_view(self, scene_id: str, npc_id: str = "") -> SceneNode:
        return SceneNode(npc_id=npc_id, scene_id=scene_id)

    @property
    def list_npcs(self) -> list[NpcNode]:
        return [self.npc_view(npc_id=npc_id) for npc_id in path_resolver.list_npc_ids()]

    @property
    def list_scenes(self) -> list[SceneNode]:
        return [self.scene_view(scene_id=scene_id) for scene_id in path_resolver.list_scene_ids()]

    def scene_override_dir(self, scene_id: str) -> Path:
        return config.OVERRIDES_SCENE_DIR / scene_id

    @property
    def data(self) -> Path:
        return config.DATA_DIR

    @property
    def prompts(self) -> PromptsNode:
        return PromptsNode()

    @property
    def session(self) -> SessionNode:
        return SessionNode(config.SESSION_PATH)

    @property
    def npc(self) -> NpcNode:
        return self.npc_view(self.session.npc_id, self.session.scene_id)

    @property
    def scene(self) -> SceneNode:
        return self.scene_view(scene_id=self.session.scene_id, npc_id=self.session.npc_id)


storage = Storage()
