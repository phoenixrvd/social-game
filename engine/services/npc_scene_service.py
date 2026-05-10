import shutil
from pathlib import Path

from engine.client import client
from engine.config import config
from engine.storage import storage


class NpcSceneService:
    @staticmethod
    def _normalize_short_description(short_description: str) -> str:
        cleaned_description = short_description.strip()
        if not cleaned_description:
            raise ValueError("Kurzbeschreibung darf nicht leer sein.")
        return cleaned_description

    @staticmethod
    def _active_context() -> tuple[str, str]:
        return storage.session.npc_id.strip(), storage.session.scene_id.strip()

    def create_override(self, short_description: str) -> Path:
        orientation = self._normalize_short_description(short_description)
        npc_id, scene_id = self._active_context()
        prompt = self._build_prompt(orientation)
        generated_scene = client.run_prompt_small(prompt).strip()
        if not generated_scene:
            raise RuntimeError("NPC-Scene-Erstellung lieferte keinen Inhalt.")
        return self._save_scene_override(npc_id, scene_id, generated_scene)

    @staticmethod
    def _build_prompt(short_description: str) -> str:
        return (
            storage.prompts.npc_scene_create_text.get()
            .strip()
            .replace("{{SHORT_DESCRIPTION}}", short_description)
            .replace("{{NPC_DESCRIPTION}}", storage.npc.description.get().strip())
            .replace("{{SCENE_DESCRIPTION}}", storage.scene.scene_original.get().strip())
        )

    @staticmethod
    def _save_scene_override(npc_id: str, scene_id: str, markdown: str) -> Path:
        target_file = config.OVERRIDES_NPC_DIR / npc_id / "scenes" / scene_id / "scene.md"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(markdown.strip() + "\n", encoding="utf-8")
        return target_file

    @staticmethod
    def delete_override(npc_id: str, scene_id: str) -> None:
        target_dir = config.OVERRIDES_NPC_DIR / npc_id / "scenes" / scene_id
        if target_dir.exists():
            shutil.rmtree(target_dir)
