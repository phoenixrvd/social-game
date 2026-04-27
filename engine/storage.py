from __future__ import annotations

import json
import yaml

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, field_validator, Field

from engine.config import config


class Message(BaseModel):
    id: str
    timestamp_utc: str
    role: Literal["user", "assistant", "system"]
    content: str

    model_config = {"str_strip_whitespace": True}

    @property
    def text_short(self) -> str:
        role_labels = {"user": "U", "assistant": "A", "system": "S"}
        return f"{role_labels[self.role]}: {self.content.strip()}"

    @property
    def text_long(self) -> str:
        return f"{self.role}: {self.content.strip()}"


def runtime_npc_scene_dir(npc_id: str, scene_id: str) -> Path:
    return config.DATA_NPC_DIR / npc_id / scene_id


def _ordered_unique_paths(*paths: Path) -> tuple[Path, ...]:
    ordered: list[Path] = []
    for path in paths:
        if path in ordered:
            continue
        ordered.append(path)
    return tuple(ordered)


def _candidate_paths(
    *,
    override_path: Path,
    default_path: Path,
    runtime_path: Path | None = None,
    fallback_path: Path | None = None,
) -> tuple[Path, ...]:
    paths: list[Path] = []
    if runtime_path is not None:
        paths.append(runtime_path)
    paths.extend([override_path, default_path])
    if fallback_path is not None:
        paths.append(fallback_path)
    return _ordered_unique_paths(*paths)


def scene_file_candidates(scene_id: str, filename: str) -> tuple[Path, ...]:
    return _candidate_paths(
        override_path=config.OVERRIDES_SCENE_DIR / scene_id / filename,
        default_path=config.SCENE_DIR / scene_id / filename,
        fallback_path=config.SCENE_DIR / config.DEFAULT_SCENE_ID / filename,
    )


def first_existing_file(candidates: tuple[Path, ...]) -> Path | None:
    for path in candidates:
        if path.is_file():
            return path
    return None


def preferred_file(candidates: tuple[Path, ...]) -> Path:
    return first_existing_file(candidates) or candidates[-1]


def npc_exists(npc_id: str) -> bool:
    return (config.OVERRIDES_NPC_DIR / npc_id).is_dir() or (config.NPC_DIR / npc_id).is_dir()


def scene_exists(scene_id: str) -> bool:
    return (config.OVERRIDES_SCENE_DIR / scene_id).is_dir() or (config.SCENE_DIR / scene_id).is_dir()


def _collect_dir_ids(*roots: Path) -> list[str]:
    ids: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        ids.update(entry.name for entry in root.iterdir() if entry.is_dir())
    return sorted(ids)


def _list_npc_ids() -> list[str]:
    return _collect_dir_ids(config.OVERRIDES_NPC_DIR, config.NPC_DIR)


def _list_scene_ids() -> list[str]:
    return _collect_dir_ids(config.OVERRIDES_SCENE_DIR, config.SCENE_DIR)


@dataclass(frozen=True)
class StorageItem(ABC):
    path: Path

    @abstractmethod
    def get(self) -> Any:
        ...

    @abstractmethod
    def save(self, value: Any) -> None:
        ...

    def is_file(self) -> bool:
        return self.path.is_file()

    def exists(self) -> bool:
        return self.path.exists()

    @property
    def name(self) -> str:
        return self.path.name


@dataclass(frozen=True)
class TextItem(StorageItem):
    def get(self) -> str:
        return self.path.read_text(encoding="utf-8") if self.path.exists() else ""

    def save(self, value: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(value, encoding="utf-8")


@dataclass(frozen=True)
class StmStorageView(StorageItem):
    def get(self, last_n: int | None = None) -> list[Message]:
        text = TextItem(self.path).get()
        messages: list[Message] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            msg = Message.model_validate(row)
            messages.append(msg)
        if last_n is None:
            return messages
        return messages[-last_n:]

    def save(self, value: list[Message]) -> None:
        payload = "".join(json.dumps(msg.model_dump(), ensure_ascii=False) + "\n" for msg in value)
        TextItem(self.path).save(payload)

    def append(self, value: Message) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(value.model_dump(), ensure_ascii=False) + "\n")

    def remove(self, value: list[Message]) -> None:
        if not value:
            return
        remove_ids = {message.id for message in value}
        kept = [message for message in self.get() if message.id not in remove_ids]
        self.save(kept)

    def as_string_short(self, last_n: int | None = None) -> str:
        """Formatiert Messages als Kurztext (Role-Labels: U/A/S)."""
        messages = self.get(last_n)
        if not messages:
            return "(keine Nachrichten)"
        return "\n".join(message.text_short for message in messages)

    def as_string_long(self, last_n: int | None = None) -> str:
        """Formatiert Messages als Langtext (volle Role-Namen)."""
        messages = self.get(last_n)
        if not messages:
            return "(keine Nachrichten)"
        return "\n".join(message.text_long for message in messages)

    def batch_messages(self) -> list[Message]:
        """Gibt Batch-Messages zurück, die verarbeitet werden sollen."""
        messages = self.get()
        messages_to_keep = config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP
        batch_size_threshold = config.UPDATER_ETM_BATCH_SIZE_THRESHOLD

        batch = messages[:-messages_to_keep] if messages_to_keep > 0 else list(messages)
        if len(batch) <= batch_size_threshold:
            return []
        return batch

    @property
    def as_batch_string(self) -> str:
        """Formatiert den zu verarbeitenden Batch als Text (mit text_short)."""
        batch = self.batch_messages()
        if not batch:
            return ""
        return "\n".join(message.text_short for message in batch)


@dataclass(frozen=True)
class YamlItem(StorageItem):
    def get(self) -> dict[str, Any]:
        return yaml.safe_load(TextItem(self.path).get()) or {}

    def save(self, value: dict[str, Any]) -> None:
        TextItem(self.path).save(yaml.safe_dump(value, allow_unicode=True, sort_keys=False))


@dataclass(frozen=True)
class ImageItem(StorageItem):
    def get(self) -> Path:
        return self.path

    def save(self, value: bytes) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(value)


class SessionState(BaseModel):
    npc_id: str = Field(default_factory=lambda: config.DEFAULT_NPC_ID)
    scene_id: str = Field(default_factory=lambda: config.DEFAULT_SCENE_ID)

    @field_validator("npc_id")
    @classmethod
    def validate_npc(cls, value: str) -> str:
        if not npc_exists(value):
            raise ValueError(f"NPC '{value}' existiert nicht.")
        return value

    @field_validator("scene_id")
    @classmethod
    def validate_scene(cls, value: str) -> str:
        if not scene_exists(value):
            raise ValueError(f"Scene '{value}' existiert nicht.")
        return value


@dataclass(frozen=True)
class SessionStorageItem(YamlItem):

    def get(self) -> SessionState:
        data = super().get() or {}
        return SessionState.model_validate(data)

    def save(
        self,
        npc_id: str | None = None,
        scene_id: str | None = None
    ) -> SessionStorageItem:
        current = self.get()

        state = SessionState(
            npc_id=npc_id if npc_id is not None else str(current.npc_id),
            scene_id=scene_id if scene_id is not None else str(current.scene_id),
        )

        YamlItem.save(self, state.model_dump())
        return self


@dataclass(frozen=True)
class PromptStorageView:
    @staticmethod
    def _resolve(filename: str) -> Path:
        return preferred_file((
            config.OVERRIDES_PROMPTS_DIR / filename,
            config.PROJECT_ROOT / "prompts" / filename,
        ))

    @property
    def image_build(self) -> TextItem:
        return TextItem(self._resolve("image_build_prompt.md"))

    @property
    def image_refresh(self) -> TextItem:
        return TextItem(self._resolve("image_refresh.md"))

    @property
    def image_scene(self) -> TextItem:
        return TextItem(self._resolve("image_scene.md"))

    @property
    def etm_update(self) -> TextItem:
        return TextItem(self._resolve("etm_update.md"))

    @property
    def chat_general_rules(self) -> TextItem:
        return TextItem(self._resolve("chat_general_rules.md"))

    @property
    def state_update(self) -> TextItem:
        return TextItem(self._resolve("state_update.md"))

    @property
    def scene_update(self) -> TextItem:
        return TextItem(self._resolve("scene_update.md"))


@dataclass(frozen=True)
class _StorageViewBase:
    npc_id: str
    scene_id: str

    @property
    def runtime_dir(self) -> Path:
        return runtime_npc_scene_dir(self.npc_id, self.scene_id)

    @staticmethod
    def _resolve_original(
        *,
        override_path: Path,
        default_path: Path,
        fallback_path: Path | None = None,
    ) -> Path:
        return preferred_file(
            _candidate_paths(
                override_path=override_path,
                default_path=default_path,
                fallback_path=fallback_path,
            )
        )

    @staticmethod
    def _resolve_resolved(
        *,
        runtime_path: Path,
        override_path: Path,
        default_path: Path,
        fallback_path: Path | None = None,
    ) -> Path:
        return preferred_file(
            _candidate_paths(
                runtime_path=runtime_path,
                override_path=override_path,
                default_path=default_path,
                fallback_path=fallback_path,
            )
        )


@dataclass(frozen=True)
class NpcStorageView(_StorageViewBase):

    @property
    def base(self) -> Path:
        return config.NPC_DIR / self.npc_id

    @property
    def base_override(self) -> Path:
        return config.OVERRIDES_NPC_DIR / self.npc_id

    @property
    def base_runtime(self) -> Path:
        return self.runtime_dir

    @property
    def default_base(self) -> Path:
        return config.NPC_DIR / config.DEFAULT_NPC_ID

    @property
    def default_scene_base(self) -> Path:
        return self.default_base / "scenes" / self.scene_id

    def _resolve_npc_original(self, filename: str) -> Path:
        return self._resolve_original(
            override_path=self.base_override / filename,
            default_path=self.base / filename,
            fallback_path=self.default_base / filename,
        )

    def _resolve_npc(self, filename: str) -> Path:
        return self._resolve_resolved(
            runtime_path=self.base_runtime / filename,
            override_path=self.base_override / filename,
            default_path=self.base / filename,
            fallback_path=self.default_base / filename,
        )

    def _resolve_npc_scene_original(self, filename: str) -> Path:
        return preferred_file(
            _ordered_unique_paths(
                self.base_override / filename,
                self.base_override / "scenes" / self.scene_id / filename,
                self.base / "scenes" / self.scene_id / filename,
                self.base / filename,
                self.default_scene_base / filename,
                self.default_base / filename,
            )
        )

    def _resolve_npc_scene(self, filename: str) -> Path:
        return preferred_file(
            _ordered_unique_paths(
                self.base_runtime / filename,
                self.base_override / filename,
                self.base_override / "scenes" / self.scene_id / filename,
                self.base / "scenes" / self.scene_id / filename,
                self.base / filename,
                self.default_scene_base / filename,
                self.default_base / filename,
            )
        )

    @property
    def description_original(self) -> TextItem:
        return TextItem(self._resolve_npc_original("description.md"))

    @property
    def description(self) -> TextItem:
        runtime_item = TextItem(self.base_runtime / "description.md")
        if runtime_item.is_file():
            return runtime_item
        resolved_original = self.description_original
        if resolved_original.is_file():
            return resolved_original
        return TextItem(self.default_base / "description.md")

    @property
    def system_prompt_original(self) -> TextItem:
        return TextItem(self._resolve_npc_original("system_prompt.md"))

    @property
    def system_prompt(self) -> TextItem:
        return TextItem(self._resolve_npc("system_prompt.md"))

    @property
    def character_original(self) -> YamlItem:
        return YamlItem(self._resolve_npc_original("character.yaml"))

    @property
    def character(self) -> YamlItem:
        return YamlItem(self._resolve_npc("character.yaml"))

    @property
    def state_runtime(self) -> TextItem:
        return TextItem(self.base_runtime / "state.md")

    @property
    def state_original(self) -> TextItem:
        return TextItem(self._resolve_npc_original("state.md"))

    @property
    def state(self) -> str:
        runtime_item = self.state_runtime
        if runtime_item.is_file():
            return runtime_item.get()

        base_state = self.state_original.get().strip()
        relationship = self.relationship.get().strip()
        return "\n\n".join(part for part in (base_state, relationship) if part)

    @property
    def relationship_original(self) -> TextItem:
        return TextItem(self._resolve_npc_original("relationship.md"))

    @property
    def relationship(self) -> TextItem:
        return self.relationship_original

    @property
    def stm(self) -> StmStorageView:
        return StmStorageView(self.base_runtime / "stm.jsonl")

    @property
    def etm_sqlite(self) -> Path:
        return self.base_runtime / "etm.sqlite"

    @property
    def img_runtime(self) -> ImageItem:
        return ImageItem(self.base_runtime / "img.png")

    @property
    def backup_dir(self) -> Path:
        return self.base_runtime / "img_backup"

    @property
    def orchestrator_dir(self) -> Path:
        return self.base_runtime / "orchestrator"

    def orchestrator_text(self, filename: str) -> TextItem:
        return TextItem(self.orchestrator_dir / filename)

    @property
    def image_prompt(self) -> TextItem:
        return TextItem(self.orchestrator_dir / "image_updater_update_prompt.txt")

    @property
    def img_original(self) -> ImageItem:
        return ImageItem(self._resolve_npc_original("img.png"))

    @property
    def scene_md_original(self) -> TextItem:
        return TextItem(self._resolve_npc_scene_original("scene.md"))

    @property
    def scene_img_original(self) -> ImageItem:
        return ImageItem(self._resolve_npc_scene_original("img.png"))

    @property
    def img_current(self) -> ImageItem:
        runtime_img = self.img_runtime
        if runtime_img.is_file():
            return runtime_img
        scene_img = self.scene_img_original
        if scene_img.is_file():
            return scene_img
        return self.img_original


@dataclass(frozen=True)
class SceneStorageView(_StorageViewBase):

    @property
    def base(self) -> Path:
        return config.SCENE_DIR / self.scene_id

    @property
    def base_override(self) -> Path:
        return config.OVERRIDES_SCENE_DIR / self.scene_id

    @property
    def base_runtime(self) -> Path:
        return self.runtime_dir

    @property
    def default_base(self) -> Path:
        return config.SCENE_DIR / config.DEFAULT_SCENE_ID

    def _resolve_scene_original(self, filename: str) -> Path:
        return self._resolve_original(
            override_path=self.base_override / filename,
            default_path=self.base / filename,
            fallback_path=self.default_base / filename,
        )

    def _resolve_scene(self, filename: str) -> Path:
        return self._resolve_resolved(
            runtime_path=self.base_runtime / filename,
            override_path=self.base_override / filename,
            default_path=self.base / filename,
            fallback_path=self.default_base / filename,
        )

    def _resolve_npc_scene_original(self, filename: str) -> Path:
        npc_base = config.NPC_DIR / self.npc_id
        npc_base_override = config.OVERRIDES_NPC_DIR / self.npc_id
        npc_default_base = config.NPC_DIR / config.DEFAULT_NPC_ID
        npc_default_scene_base = npc_default_base / "scenes" / self.scene_id
        return preferred_file(
            _ordered_unique_paths(
                npc_base_override / filename,
                npc_base_override / "scenes" / self.scene_id / filename,
                npc_base / "scenes" / self.scene_id / filename,
                npc_base / filename,
                npc_default_scene_base / filename,
                npc_default_base / filename,
            )
        )

    @property
    def scene_runtime(self) -> TextItem:
        return TextItem(self.base_runtime / "scene.md")

    @property
    def scene_original(self) -> TextItem:
        return TextItem(self._resolve_scene_original("scene.md"))

    @property
    def scene(self) -> TextItem:
        return TextItem(self._resolve_scene("scene.md"))

    @property
    def npc_scene_original(self) -> TextItem:
        return TextItem(self._resolve_npc_scene_original("scene.md"))

    @property
    def description(self) -> str:
        runtime_scene = self.scene_runtime
        if runtime_scene.is_file():
            return runtime_scene.get()
        description = self.scene_original.get()
        npc_scene = self.npc_scene_original
        if npc_scene.is_file():
            return "\n".join([description, npc_scene.get()])
        return description

    @property
    def img_original(self) -> ImageItem:
        return ImageItem(self._resolve_scene_original("img.png"))

    @property
    def img(self) -> Path:
        return self.img_original.get()


class Storage:
    def npc_view(self, npc_id: str, scene_id: str) -> NpcStorageView:
        return NpcStorageView(npc_id=npc_id, scene_id=scene_id)

    def scene_view(self, npc_id: str, scene_id: str) -> SceneStorageView:
        return SceneStorageView(npc_id=npc_id, scene_id=scene_id)

    def list_npcs(self) -> list[NpcStorageView]:
        return [self.npc_view(npc_id=npc_id, scene_id="") for npc_id in _list_npc_ids()]

    def list_scenes(self) -> list[SceneStorageView]:
        return [self.scene_view(npc_id="", scene_id=scene_id) for scene_id in _list_scene_ids()]

    @property
    def data(self) -> Path:
        return config.DATA_DIR

    @property
    def etm_fastembed_cache(self) -> Path:
        return config.DATA_DIR / "fastembed_cache"

    @property
    def overrides_root(self) -> Path:
        return config.OVERRIDES_DIR

    @property
    def prompts(self) -> PromptStorageView:
        return PromptStorageView()

    @property
    def session(self) -> SessionStorageItem:
        return SessionStorageItem(config.SESSION_PATH)

    @property
    def npc(self) -> NpcStorageView:
        session = self.session.get()
        return self.npc_view(
            npc_id=session.npc_id,
            scene_id=session.scene_id,
        )

    @property
    def scene(self) -> SceneStorageView:
        session = self.session.get()
        return self.scene_view(
            npc_id=session.npc_id,
            scene_id=session.scene_id,
        )


storage = Storage()
