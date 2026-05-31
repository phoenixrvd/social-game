import shutil
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from engine.client import client
from engine.config import config
from engine.services.id_normalizer import normalize_to_snake_id
from engine.storage import storage


class NpcDescriptionDraft(BaseModel):
    character_name: str = Field(min_length=1, max_length=48)
    grounding_sentence: str = Field(min_length=1)
    external_traits: list[str] = Field(min_length=3, max_length=5)
    inner_traits: list[str] = Field(min_length=3, max_length=5)
    core_dynamics: list[str] = Field(min_length=3, max_length=5)
    behavior_rules: list[str] = Field(min_length=4, max_length=6)
    stress_reactions: list[str] = Field(min_length=3, max_length=5)
    subtext_rules: list[str] = Field(min_length=3, max_length=5)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("grounding_sentence")
    @classmethod
    def validate_description_text(cls, value: str) -> str:
        if "�" in value or "1??" in value:
            raise ValueError("NPC-Beschreibung enthaelt ungueltige Zeichen.")
        return value

    @field_validator(
        "external_traits",
        "inner_traits",
        "core_dynamics",
        "behavior_rules",
        "stress_reactions",
        "subtext_rules",
    )
    @classmethod
    def validate_description_list(cls, values: list[str]) -> list[str]:
        if any("�" in value or "1??" in value for value in values):
            raise ValueError("NPC-Beschreibung enthaelt ungueltige Zeichen.")
        return values

    @property
    def description_markdown(self) -> str:
        lines = ["# Charakter", "", self.grounding_sentence]
        sections = [
            ("Außen:", self.external_traits),
            ("Innen:", self.inner_traits),
            ("Kerndynamik:", self.core_dynamics),
            ("# Verhalten", self.behavior_rules),
            ("# Stressreaktion", self.stress_reactions),
            ("# Subtext", self.subtext_rules),
        ]
        for heading, values in sections:
            lines.extend(["", heading, "", *self._bullets(values)])
        return "\n".join(lines)

    @staticmethod
    def _bullets(values: list[str]) -> list[str]:
        return [f"- {value}" for value in values]


class NpcStateDraft(BaseModel):
    trust: int = Field(ge=0, le=100)
    comfort: int = Field(ge=0, le=100)
    interest: int = Field(ge=0, le=100)
    mood: str = Field(min_length=1, max_length=24)
    relationship_stage: str = Field(min_length=1, max_length=48)
    state_bullets: list[str] = Field(min_length=3, max_length=5)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("mood")
    @classmethod
    def validate_mood(cls, value: str) -> str:
        if value != value.lower() or " " in value:
            raise ValueError("NPC-State mood muss ein kurzer lowercase-Wert sein.")
        if "�" in value:
            raise ValueError("NPC-State enthaelt ungueltige Zeichen.")
        return value

    @field_validator("relationship_stage")
    @classmethod
    def validate_relationship_stage(cls, value: str) -> str:
        if "�" in value:
            raise ValueError("NPC-State enthaelt ungueltige Zeichen.")
        return value

    @field_validator("state_bullets")
    @classmethod
    def validate_state_bullets(cls, values: list[str]) -> list[str]:
        if any("�" in value for value in values):
            raise ValueError("NPC-State enthaelt ungueltige Zeichen.")
        return values

    @property
    def state_markdown(self) -> str:
        bullets = [f"- {value}" for value in self.state_bullets]
        return "\n".join([
            "---",
            f"trust: {self.trust}",
            f"comfort: {self.comfort}",
            f"interest: {self.interest}",
            f"mood: {self.mood}",
            f"relationship_stage: {self.relationship_stage}",
            "---",
            "",
            *bullets,
        ])


class NpcService:
    @staticmethod
    def _normalize_name(character_name: str) -> tuple[str, str]:
        cleaned_name = character_name.strip()
        npc_id = normalize_to_snake_id(cleaned_name)
        if not npc_id:
            raise ValueError("NPC-Name ergibt keine gueltige ID.")
        return cleaned_name, npc_id

    def create_override(self, character_description: str, npc_image_bytes: bytes | None = None) -> Path:
        orientation = character_description.strip()
        if not orientation:
            raise ValueError("Charakterbeschreibung darf nicht leer sein.")
        description_draft = self._create_description_draft(orientation)
        state_draft = self._create_state_draft(description_draft.description_markdown)
        cleaned_name, npc_id = self._normalize_name(description_draft.character_name)
        target_dir = self._next_available_dir(npc_id)
        target_dir.mkdir(parents=True, exist_ok=False)
        self._save_npc_files(target_dir, cleaned_name, description_draft, state_draft)
        self._save_npc_image(target_dir, description_draft.description_markdown, npc_image_bytes)
        return target_dir

    def describe_reference_image(self, reference_image_bytes: bytes) -> str:
        description = client.describe_npc_reference_img(
            storage.prompts.npc_describe_image.get().strip(),
            reference_image_bytes,
        ).strip()
        if not description:
            raise RuntimeError("Bildbeschreibung blieb leer.")
        return description

    def create_preview_image(self, npc_description: str, reference_image_bytes: bytes | None = None) -> bytes:
        description = npc_description.strip()
        if not description:
            raise ValueError("Charakterbeschreibung darf nicht leer sein.")
        if reference_image_bytes is None:
            return client.generate_scene_img(self._build_image_prompt(description))
        return client.generate_npc_img_from_reference(self._build_reference_image_prompt(description), reference_image_bytes)

    def _create_description_draft(self, character_description: str) -> NpcDescriptionDraft:
        prompt = self._build_description_prompt(character_description)
        return client.run_prompt_small_model(prompt, NpcDescriptionDraft)

    def _create_state_draft(self, npc_description: str) -> NpcStateDraft:
        prompt = self._build_state_prompt(npc_description)
        return client.run_prompt_small_model(prompt, NpcStateDraft)

    @staticmethod
    def _build_description_prompt(character_description: str) -> str:
        return (
            storage.prompts.npc_create_description.get()
            .strip()
            .replace("{{CHARACTER_DESCRIPTION}}", character_description)
        )

    @staticmethod
    def _build_state_prompt(npc_description: str) -> str:
        return storage.prompts.npc_create_state.get().strip().replace("{{NPC_DESCRIPTION}}", npc_description)

    @staticmethod
    def _build_image_prompt(npc_description: str) -> str:
        return (
            storage.prompts.npc_create_image.get()
            .strip()
            .replace("{{IMAGE_STYLE_RULES}}", storage.prompts.image_style_rules.get().strip())
            .replace("{{NPC_DESCRIPTION}}", npc_description)
        )

    @classmethod
    def _build_reference_image_prompt(cls, npc_description: str) -> str:
        return (
            storage.prompts.npc_create_image_from_reference.get()
            .strip()
            .replace("{{IMAGE_STYLE_RULES}}", storage.prompts.image_style_rules.get().strip())
            .replace("{{NPC_DESCRIPTION}}", npc_description)
        )

    @staticmethod
    def _next_available_dir(npc_id: str) -> Path:
        for suffix in range(0, 10_000):
            candidate_id = npc_id if suffix == 0 else f"{npc_id}_{suffix}"
            candidate_dir = config.OVERRIDES_NPC_DIR / candidate_id
            if not candidate_dir.exists():
                return candidate_dir
        raise RuntimeError("Konnte kein freies NPC-Verzeichnis finden.")

    @staticmethod
    def _save_npc_files(
        target_dir: Path,
        character_name: str,
        description_draft: NpcDescriptionDraft,
        state_draft: NpcStateDraft,
    ) -> None:
        payload = yaml.safe_dump({"name": character_name}, allow_unicode=True, sort_keys=False)
        (target_dir / "character.yaml").write_text(payload, encoding="utf-8")
        (target_dir / "description.md").write_text(description_draft.description_markdown.strip() + "\n", encoding="utf-8")
        (target_dir / "state.md").write_text(state_draft.state_markdown.strip() + "\n", encoding="utf-8")

    def _save_npc_image(self, target_dir: Path, npc_description: str, npc_image_bytes: bytes | None = None) -> None:
        if npc_image_bytes is not None:
            (target_dir / "img.png").write_bytes(npc_image_bytes)
            return
        prompt = self._build_image_prompt(npc_description)
        (target_dir / "img.png").write_bytes(client.generate_scene_img(prompt))

    @staticmethod
    def reset_active_runtime() -> None:
        session = storage.session
        scene_data_dir = storage.npc_view(
            npc_id=session.npc_id,
            scene_id=session.scene_id,
        ).base_runtime
        if scene_data_dir.exists():
            shutil.rmtree(scene_data_dir)

    @staticmethod
    def reset_npc_artifacts(npc_id: str) -> None:
        npc_view = storage.npc_view(npc_id=npc_id)

        npc_runtime_dir = npc_view.base_runtime
        if npc_runtime_dir.exists():
            shutil.rmtree(npc_runtime_dir)

        npc_scene_overrides_dir = npc_view.override_base / "scenes"
        if npc_scene_overrides_dir.exists():
            shutil.rmtree(npc_scene_overrides_dir)

    @staticmethod
    def delete_dynamic_npc_artifacts(npc_id: str) -> None:
        if not storage.npc.is_dynamic_npc:
            raise ValueError("Aktiver NPC ist kein erstellter NPC.")
        if storage.session.npc_id == npc_id:
            storage.session.npc_id = config.DEFAULT_NPC_ID
        if (config.NPC_DIR / npc_id).is_dir():
            return
        override_dir = config.OVERRIDES_NPC_DIR / npc_id
        runtime_dir = config.DATA_NPC_DIR / npc_id
        if override_dir.exists():
            shutil.rmtree(override_dir)
        if runtime_dir.exists():
            shutil.rmtree(runtime_dir)
