from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
import yaml

from engine.config import config

if TYPE_CHECKING:
    from engine.models import Session


def runtime_npc_scene_dir(npc_id: str, scene_id: str) -> Path:
    return config.DATA_NPC_DIR / npc_id / scene_id


def _original_candidates(default_path: Path, override_path: Path) -> tuple[Path, ...]:
    return override_path, default_path


def _resolved_candidates(runtime_path: Path, override_path: Path, default_path: Path) -> tuple[Path, ...]:
    return runtime_path, override_path, default_path


def scene_file_candidates(scene_id: str, filename: str) -> tuple[Path, ...]:
    return _original_candidates(
        default_path=config.SCENE_DIR / scene_id / filename,
        override_path=config.OVERRIDES_SCENE_DIR / scene_id / filename,
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
class JsonlItem(StorageItem):
    def get(self) -> list[dict[str, Any]]:
        text = TextItem(self.path).get()
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    def save(self, value: list[dict[str, Any]]) -> None:
        payload = "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in value)
        TextItem(self.path).save(payload)

    def append(self, value: dict[str, Any]) -> None:
        existing = TextItem(self.path).get()
        TextItem(self.path).save(existing + json.dumps(value, ensure_ascii=True) + "\n")


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
    ) -> Path:
        return preferred_file(_original_candidates(default_path=default_path, override_path=override_path))

    @staticmethod
    def _resolve_resolved(
        *,
        runtime_path: Path,
        override_path: Path,
        default_path: Path,
    ) -> Path:
        return preferred_file(
            _resolved_candidates(
                runtime_path=runtime_path,
                override_path=override_path,
                default_path=default_path,
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

    def _resolve_npc_original(self, filename: str) -> Path:
        return self._resolve_original(
            override_path=self.base_override / filename,
            default_path=self.base / filename,
        )

    def _resolve_npc(self, filename: str) -> Path:
        return self._resolve_resolved(
            runtime_path=self.base_runtime / filename,
            override_path=self.base_override / filename,
            default_path=self.base / filename,
        )

    def _resolve_npc_scene_original(self, filename: str) -> Path:
        return self._resolve_original(
            override_path=self.base_override / "scenes" / self.scene_id / filename,
            default_path=self.base / "scenes" / self.scene_id / filename,
        )

    def _resolve_npc_scene(self, filename: str) -> Path:
        return self._resolve_resolved(
            runtime_path=self.base_runtime / filename,
            override_path=self.base_override / "scenes" / self.scene_id / filename,
            default_path=self.base / "scenes" / self.scene_id / filename,
        )

    @property
    def description_original(self) -> TextItem:
        return TextItem(self._resolve_npc_original("description.md"))

    @property
    def description(self) -> TextItem:
        return TextItem(self._resolve_npc("description.md"))

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
    def state(self) -> TextItem:
        return TextItem(self._resolve_npc("state.md"))

    @property
    def relationship_original(self) -> TextItem:
        return TextItem(self._resolve_npc_original("relationship.md"))

    @property
    def relationship(self) -> TextItem:
        return self.relationship_original

    @property
    def stm(self) -> JsonlItem:
        return JsonlItem(self.base_runtime / "stm.jsonl")

    @property
    def etm_chroma(self) -> Path:
        return self.base_runtime / "etm.chroma"

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

    def _resolve_scene_original(self, filename: str) -> Path:
        return self._resolve_original(
            override_path=self.base_override / filename,
            default_path=self.base / filename,
        )

    def _resolve_scene(self, filename: str) -> Path:
        return self._resolve_resolved(
            runtime_path=self.base_runtime / filename,
            override_path=self.base_override / filename,
            default_path=self.base / filename,
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
    def img_original(self) -> ImageItem:
        return ImageItem(self._resolve_scene_original("img.png"))

    @property
    def img(self) -> ImageItem:
        return ImageItem(self._resolve_scene("img.png"))


class Storage:
    def __init__(self) -> None:
        self._npc_view: NpcStorageView | None = None
        self._scene_view: SceneStorageView | None = None

    def npc_view(self, npc_id: str, scene_id: str) -> NpcStorageView:
        return NpcStorageView(npc_id=npc_id, scene_id=scene_id)

    def scene_view(self, npc_id: str, scene_id: str) -> SceneStorageView:
        return SceneStorageView(npc_id=npc_id, scene_id=scene_id)

    def list_npcs(self) -> list[NpcStorageView]:
        return [self.npc_view(npc_id=npc_id, scene_id="") for npc_id in _list_npc_ids()]

    def list_scenes(self) -> list[SceneStorageView]:
        return [self.scene_view(npc_id="", scene_id=scene_id) for scene_id in _list_scene_ids()]

    def bootstrap(self, npc_id: str, scene_id: str) -> None:
        self._npc_view = self.npc_view(npc_id, scene_id)
        self._scene_view = self.scene_view(npc_id, scene_id)

    def _ensure_bootstrapped(self) -> None:
        session = self._session()
        if self._npc_view is None or self._scene_view is None:
            self.bootstrap(session.npc_id, session.scene_id)
            return
        if self._npc_view.npc_id != session.npc_id or self._npc_view.scene_id != session.scene_id:
            self.bootstrap(session.npc_id, session.scene_id)

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
    def session(self) -> YamlItem:
        return YamlItem(config.SESSION_PATH)

    @property
    def npc(self) -> NpcStorageView:
        self._ensure_bootstrapped()
        assert self._npc_view is not None
        return self._npc_view

    @property
    def scene(self) -> SceneStorageView:
        self._ensure_bootstrapped()
        assert self._scene_view is not None
        return self._scene_view

    @staticmethod
    def _session() -> Session:
        from engine.stores.session_store import SessionStore

        return SessionStore().load()


storage = Storage()
