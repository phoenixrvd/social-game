from __future__ import annotations

from pathlib import Path

from engine.config import config
from engine.client import client
from engine.services.etm_service import EtmService
from engine.services.id_normalizer import normalize_to_snake_id
from engine.storage import storage


class SceneService:
    def __init__(self) -> None:
        self.etm_retrieval = EtmService()

    @staticmethod
    def _normalize_id(scene_name: str) -> str:
        scene_id = normalize_to_snake_id(scene_name)
        if not scene_id:
            raise ValueError("Scene-Name ergibt keine gueltige ID.")
        return scene_id

    def run_update(self) -> str:
        prompt = self._build_prompt()
        scene = client.run_prompt_small(prompt).strip()

        storage.scene.scene_runtime.save(scene)
        return scene

    def create_override(self, scene_name: str) -> Path:
        scene_id = self._normalize_id(scene_name)
        target_dir = config.OVERRIDES_SCENE_DIR / scene_id
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def _build_prompt(self) -> str:
        stm_text = storage.npc.stm.text_latest
        etm_text = self.etm_retrieval.load_relevant(stm_text)
        return (
            storage.prompts.scene_update.get().strip()
            .replace("{{SCENE_DATA}}", storage.scene.description.strip())
            .replace("{{SHORT_TERM_MEMORY}}", stm_text)
            .replace("{{CURRENT_ETM}}", etm_text)
        )
