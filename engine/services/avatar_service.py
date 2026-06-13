from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from engine.client import client
from engine.config import config
from engine.services.id_normalizer import normalize_to_snake_id
from engine.services.npc_service import NpcService
from engine.storage import storage


class AvatarDescriptionDraft(BaseModel):
    character_name: str = Field(min_length=1, max_length=48)
    profile_markdown: str = Field(min_length=1, max_length=1_200)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("profile_markdown")
    @classmethod
    def validate_profile_markdown(cls, value: str) -> str:
        if "�" in value or "1??" in value:
            raise ValueError("Avatar-Beschreibung enthält ungültige Zeichen.")
        forbidden_terms = (
            "# Verhalten",
            "# Stressreaktion",
            "# Subtext",
            "Kerndynamik",
            "Gesprächsstil",
            "Rollenspiel",
        )
        if any(term.lower() in value.lower() for term in forbidden_terms):
            raise ValueError("Avatar-Beschreibung enthält NPC-Profilabschnitte.")
        return value


class AvatarService:
    def __init__(self) -> None:
        self.npc_service = NpcService()

    def create_override(self, character_description: str, avatar_image_bytes: bytes | None = None) -> Path:
        orientation = character_description.strip()
        if not orientation:
            raise ValueError("Charakterbeschreibung darf nicht leer sein.")
        description_draft = self._create_description_draft(orientation)
        cleaned_name, avatar_id = self._normalize_name(description_draft.character_name)
        target_dir = self._next_available_dir(avatar_id)
        target_dir.mkdir(parents=True, exist_ok=False)
        self._save_avatar_files(target_dir, target_dir.name, cleaned_name, description_draft.profile_markdown)
        self._save_avatar_image(target_dir, description_draft.profile_markdown, avatar_image_bytes)
        return target_dir

    def update_avatar(self, avatar_id: str, description: str, avatar_image_bytes: bytes | None = None) -> Path:
        text = description.strip()
        if not text:
            raise ValueError("Charakterbeschreibung darf nicht leer sein.")
        avatar_view = storage.avatar_view(avatar_id)
        character = avatar_view.character.get()
        name = str(character.get("name", "")).strip() or avatar_id.replace("_", " ").title()
        target_dir = config.OVERRIDES_AVATAR_DIR / avatar_id
        target_dir.mkdir(parents=True, exist_ok=True)
        current_image = avatar_view.img.get().read_bytes()
        self._save_avatar_files(target_dir, avatar_id, name, text)
        (target_dir / "img.png").write_bytes(avatar_image_bytes if avatar_image_bytes is not None else current_image)
        return target_dir

    def describe_reference_image(self, reference_image_bytes: bytes) -> str:
        description = client.describe_npc_reference_img(
            storage.prompts.avatar_describe_image.get().strip(),
            reference_image_bytes,
        ).strip()
        if not description:
            raise RuntimeError("Bildbeschreibung blieb leer.")
        return description

    def create_preview_image(self, avatar_description: str, reference_image_bytes: bytes | None = None) -> bytes:
        return self.npc_service.create_preview_image(avatar_description, reference_image_bytes)

    @staticmethod
    def _create_description_draft(character_description: str) -> AvatarDescriptionDraft:
        return client.run_prompt_small_model(AvatarService._build_description_prompt(character_description), AvatarDescriptionDraft)

    @staticmethod
    def _build_description_prompt(character_description: str) -> str:
        return storage.prompts.avatar_create_description.get().strip().replace(
            "{{CHARACTER_DESCRIPTION}}",
            character_description.strip(),
        )

    @staticmethod
    def delete_dynamic_avatar_artifacts(avatar_id: str) -> None:
        avatar_view = storage.avatar_view(avatar_id)
        if not avatar_view.is_dynamic_avatar:
            raise ValueError("Standard-Avatar kann nicht gelöscht werden.")
        if storage.session.avatar_id == avatar_id:
            storage.session.avatar_id = config.DEFAULT_AVATAR_ID
        override_dir = config.OVERRIDES_AVATAR_DIR / avatar_id
        if override_dir.exists():
            shutil.rmtree(override_dir)

    @staticmethod
    def can_reset_avatar(avatar_id: str) -> bool:
        return (config.AVATAR_DIR / avatar_id).is_dir() and (config.OVERRIDES_AVATAR_DIR / avatar_id).exists()

    @staticmethod
    def reset_avatar_artifacts(avatar_id: str) -> None:
        if not AvatarService.can_reset_avatar(avatar_id):
            raise ValueError("Avatar kann nicht zurückgesetzt werden.")
        shutil.rmtree(config.OVERRIDES_AVATAR_DIR / avatar_id)

    @staticmethod
    def _normalize_name(character_name: str) -> tuple[str, str]:
        cleaned_name = character_name.strip() or "Avatar"
        avatar_id = normalize_to_snake_id(cleaned_name)
        if not avatar_id:
            cleaned_name = "Avatar"
            avatar_id = "avatar"
        return cleaned_name, avatar_id

    @staticmethod
    def _next_available_dir(avatar_id: str) -> Path:
        for suffix in range(0, 10_000):
            candidate_id = avatar_id if suffix == 0 else f"{avatar_id}_{suffix}"
            candidate_dir = config.OVERRIDES_AVATAR_DIR / candidate_id
            if not candidate_dir.exists() and not (config.AVATAR_DIR / candidate_id).exists():
                return candidate_dir
        raise RuntimeError("Konnte kein freies Avatar-Verzeichnis finden.")

    @staticmethod
    def _save_avatar_files(target_dir: Path, avatar_id: str, character_name: str, description: str) -> None:
        payload = yaml.safe_dump({"id": avatar_id, "name": character_name}, allow_unicode=True, sort_keys=False)
        (target_dir / "character.yaml").write_text(payload, encoding="utf-8")
        (target_dir / "description.md").write_text(description.strip() + "\n", encoding="utf-8")

    def _save_avatar_image(self, target_dir: Path, avatar_description: str, avatar_image_bytes: bytes | None = None) -> None:
        if avatar_image_bytes is not None:
            (target_dir / "img.png").write_bytes(avatar_image_bytes)
            return
        (target_dir / "img.png").write_bytes(self.create_preview_image(avatar_description))
