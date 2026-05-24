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

    def create_override(self, short_description: str) -> Path:
        npc_id = storage.session.npc_id.strip()
        scene_id = storage.session.scene_id.strip()
        generated_scene = self.generate_context(short_description)
        return self._save_scene_override(npc_id, scene_id, generated_scene)

    def generate_context(self, short_description: str) -> str:
        orientation = self._normalize_short_description(short_description)
        prompt = self._build_prompt(orientation)
        generated_scene = client.run_prompt_small(prompt).strip()
        if not generated_scene:
            raise RuntimeError("NPC-Scene-Erstellung lieferte keinen Inhalt.")
        return generated_scene

    def save_active_context(self, markdown: str) -> Path:
        target_file = storage.scene.npc_context.override
        target_file.save(markdown)
        return target_file.path

    def adapt_default_fallback(self) -> Path | None:
        if storage.session.npc_id == config.DEFAULT_NPC_ID:
            return None
        if storage.scene.npc_context.existing_file is not None:
            return None
        default_context = storage.scene_view(config.DEFAULT_NPC_ID, storage.session.scene_id).npc_context.existing_file
        if default_context is None:
            return None
        prompt = self._build_adapt_prompt(default_context.get())
        generated_scene = client.run_prompt_small(prompt).strip()
        if not generated_scene:
            raise RuntimeError("NPC-Scene-Fallback-Adaptierung lieferte keinen Inhalt.")
        target_file = storage.scene.npc_context.override
        target_file.save(generated_scene.strip() + "\n")
        return target_file.path

    @staticmethod
    def _build_prompt(short_description: str) -> str:
        return (
            storage.prompts.npc_scene_create_text.get()
            .strip()
            .replace("{{SHORT_DESCRIPTION}}", short_description)
            .replace("{{NPC_DESCRIPTION}}", storage.npc.description.get().strip())
            .replace("{{SCENE_DESCRIPTION}}", storage.scene.location.original.get().strip())
        )

    @staticmethod
    def _save_scene_override(npc_id: str, scene_id: str, markdown: str) -> Path:
        target_file = storage.scene_view(npc_id=npc_id, scene_id=scene_id).npc_context.override
        target_file.save(markdown.strip() + "\n")
        return target_file.path

    @staticmethod
    def _build_adapt_prompt(default_context: str) -> str:
        return (
            storage.prompts.npc_scene_adapt_default_text.get()
            .strip()
            .replace("{{NPC_DESCRIPTION}}", storage.npc.description.get().strip())
            .replace("{{SCENE_DESCRIPTION}}", storage.scene.location.original.get().strip())
            .replace("{{DEFAULT_NPC_SCENE_DESCRIPTION}}", default_context.strip())
        )

    @staticmethod
    def delete_override(npc_id: str, scene_id: str) -> None:
        target_dir = storage.scene_view(npc_id=npc_id, scene_id=scene_id).npc_context.override.path.parent
        if target_dir.exists():
            shutil.rmtree(target_dir)
