from __future__ import annotations

from pathlib import Path
import shutil

from pydantic import BaseModel, ConfigDict, Field

from engine.config import config
from engine.client import client
from engine.services.etm_service import EtmService
from engine.services.id_normalizer import normalize_to_snake_id
from engine.services.npc_scene_service import NpcSceneService
from engine.services.npc_service import NpcService
from engine.storage import storage


class SceneDraft(BaseModel):
    location_name: str = Field(min_length=1, max_length=48)
    scene_description: str = Field(min_length=1)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SceneService:
    def __init__(self) -> None:
        self.etm_retrieval = EtmService()

    @staticmethod
    def _normalize_short_description(short_description: str) -> str:
        cleaned_description = short_description.strip()
        if not cleaned_description:
            raise ValueError("Kurzbeschreibung darf nicht leer sein.")
        return cleaned_description

    def run_update(self) -> str:
        prompt = self._build_prompt()
        scene = client.run_prompt_small(prompt).strip()

        storage.scene.location.runtime.save(scene)
        return scene

    def create_override(self, short_description: str, scene_image_bytes: bytes | None = None) -> Path:
        orientation = self._normalize_short_description(short_description)
        scene_draft = self._create_scene_draft(orientation)
        target_dir = self._next_available_dir(scene_draft.location_name)
        target_dir.mkdir(parents=True, exist_ok=False)
        self._save_scene_markdown(target_dir, scene_draft)
        self._save_scene_image(target_dir, scene_draft, scene_image_bytes)
        return target_dir

    def update_active_override(self, short_description: str, scene_image_bytes: bytes | None = None) -> Path:
        orientation = self._normalize_short_description(short_description)
        scene_draft = self._create_scene_draft(orientation)
        location = storage.scene.location
        location.override.path.parent.mkdir(parents=True, exist_ok=True)
        location.override.save(f"## {scene_draft.location_name}\n\n{scene_draft.scene_description}\n")
        if scene_image_bytes is not None:
            location.img_override.save(scene_image_bytes)
            return location.override.path.parent
        prompt = self._build_scene_image_prompt(scene_draft)
        location.img_override.save(client.generate_scene_img(prompt))
        return location.override.path.parent

    def describe_reference_image(self, reference_image_bytes: bytes) -> str:
        description = client.describe_scene_reference_img(
            storage.prompts.scene_describe_image.get().strip(),
            reference_image_bytes,
        ).strip()
        if not description:
            raise RuntimeError("Bildbeschreibung blieb leer.")
        return description

    def create_preview_image(self, scene_description: str, reference_image_bytes: bytes | None = None) -> bytes:
        description = self._normalize_short_description(scene_description)
        scene_draft = SceneDraft(location_name="Neue Location", scene_description=description)
        prompt = self._build_scene_image_prompt(scene_draft)
        if reference_image_bytes is None:
            return client.generate_scene_img(prompt)
        return client.generate_scene_img_from_reference(prompt, reference_image_bytes)

    def resolve_create_image(
        self,
        scene_description: str,
        image_bytes: bytes | None,
        reference_image_bytes: bytes | None,
    ) -> bytes | None:
        if image_bytes is not None:
            return image_bytes
        if reference_image_bytes is None:
            return None
        return self.create_preview_image(scene_description, reference_image_bytes)

    def _create_scene_draft(self, short_description: str) -> SceneDraft:
        prompt = self._build_scene_create_prompt(short_description)
        return client.run_prompt_small_model(prompt, SceneDraft)

    @staticmethod
    def _build_scene_create_prompt(short_description: str) -> str:
        return storage.prompts.scene_create_text.get().strip().replace("{{SHORT_DESCRIPTION}}", short_description)

    def _next_available_dir(self, location_name: str) -> Path:
        base_id = self._normalize_location_id(location_name)
        for suffix in range(0, 10_000):
            candidate_id = base_id if suffix == 0 else f"{base_id}_{suffix}"
            candidate_dir = config.OVERRIDES_SCENE_DIR / candidate_id
            if not candidate_dir.exists():
                return candidate_dir
        raise RuntimeError("Konnte kein freies Scene-Verzeichnis finden.")

    @staticmethod
    def _normalize_location_id(location_name: str) -> str:
        scene_id = normalize_to_snake_id(location_name.strip())
        if not scene_id:
            raise ValueError("Scene-Name ergibt keine gueltige ID.")
        return scene_id

    def _save_scene_markdown(self, target_dir: Path, scene_draft: SceneDraft) -> None:
        markdown = f"## {scene_draft.location_name}\n\n{scene_draft.scene_description}\n"
        (target_dir / "scene.md").write_text(markdown, encoding="utf-8")

    def _save_scene_image(self, target_dir: Path, scene_draft: SceneDraft, scene_image_bytes: bytes | None = None) -> None:
        if scene_image_bytes is not None:
            (target_dir / "img.png").write_bytes(scene_image_bytes)
            return
        prompt = self._build_scene_image_prompt(scene_draft)
        (target_dir / "img.png").write_bytes(client.generate_scene_img(prompt))

    @staticmethod
    def _build_scene_image_prompt(scene_draft: SceneDraft) -> str:
        return (
            storage.prompts.scene_create_image.get()
            .strip()
            .replace("{{SCENE_NAME}}", scene_draft.location_name)
            .replace("{{SCENE_DESCRIPTION}}", scene_draft.scene_description)
        )

    def _build_prompt(self) -> str:
        stm_text = storage.npc.stm.text_latest
        etm_text = self.etm_retrieval.load_relevant(stm_text)
        return (
            storage.prompts.scene_update.get().strip()
            .replace("{{SCENE_DATA}}", storage.scene.description.strip())
            .replace("{{SHORT_TERM_MEMORY}}", stm_text)
            .replace("{{CURRENT_ETM}}", etm_text)
        )

    @staticmethod
    def delete_dynamic_scene(scene_id: str) -> None:
        if not (config.OVERRIDES_SCENE_DIR / scene_id).is_dir():
            raise ValueError("Szene ist keine erstellte Szene.")

        try:
            is_active_scene = storage.session.scene_id == scene_id
        except ValueError:
            is_active_scene = False

        if is_active_scene:
            session_data = storage.session._yaml.get() or {}
            session_data["scene_id"] = config.DEFAULT_SCENE_ID
            storage.session._yaml.save(session_data)

        SceneService.reset_scene_artifacts(scene_id)
        scene_override_dir = config.OVERRIDES_SCENE_DIR / scene_id
        if scene_override_dir.exists():
            shutil.rmtree(scene_override_dir)

    @staticmethod
    def can_reset_active_scene() -> bool:
        scene_id = storage.session.scene_id
        default_scene_dir = config.SCENE_DIR / scene_id
        override_scene_dir = config.OVERRIDES_SCENE_DIR / scene_id
        if not default_scene_dir.is_dir() or storage.scene.location.is_dynamic:
            return False
        if override_scene_dir.exists():
            return True
        for npc in storage.list_npcs:
            scene_view = storage.scene_view(scene_id, npc.npc_id)
            npc_view = storage.npc_view(npc.npc_id, scene_id)
            if npc_view.base_runtime.exists() or scene_view.npc_context.override.path.parent.exists():
                return True
        return False

    @staticmethod
    def reset_active_scene_artifacts(scene_id: str) -> None:
        if not SceneService.can_reset_active_scene():
            raise ValueError("Aktive Szene kann nicht zurückgesetzt werden.")
        SceneService.reset_scene_artifacts(scene_id)

    @staticmethod
    def reset_active() -> None:
        from engine.tools.scheduler import get_scheduler

        scene_id = storage.session.scene_id
        if not SceneService.can_reset_active_scene():
            raise ValueError("Aktive Szene kann nicht zurückgesetzt werden.")
        get_scheduler().clear_pending_jobs()
        NpcService.reset_active_runtime()
        SceneService.reset_active_scene_artifacts(scene_id)

    @staticmethod
    def reset_scene_artifacts(scene_id: str) -> None:
        SceneService._delete_dynamic_scene_overrides(scene_id)
        SceneService._delete_dynamic_scene_runtime(scene_id)

    @staticmethod
    def _delete_dynamic_scene_overrides(scene_id: str) -> None:
        scene_override_dir = config.OVERRIDES_SCENE_DIR / scene_id
        if scene_override_dir.exists():
            shutil.rmtree(scene_override_dir)

        for npc in storage.list_npcs:
            NpcSceneService.delete_override(npc_id=npc.npc_id, scene_id=scene_id)

    @staticmethod
    def _delete_dynamic_scene_runtime(scene_id: str) -> None:
        for npc in storage.list_npcs:
            scene_runtime_dir = storage.npc_view(npc_id=npc.npc_id, scene_id=scene_id).base_runtime
            if scene_runtime_dir.exists():
                shutil.rmtree(scene_runtime_dir)
