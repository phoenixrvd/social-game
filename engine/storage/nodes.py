from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from engine.config import config
from engine.storage.files import ImageFile, TextFile, YamlFile
from engine.storage.models import Episode, Message, SessionState
from engine.storage.paths import path_resolver
from engine.storage.stores import _EtmSqliteStore, _StmJsonlStore


@dataclass(frozen=True)
class StmNode:
    path: Path

    @property
    def _store(self) -> _StmJsonlStore:
        return _StmJsonlStore(self.path)

    def get(self, last_n: int | None = None) -> list[Message]:
        messages = self._store.load()
        if last_n is None:
            return messages
        return messages[-last_n:]

    @property
    def latest(self) -> list[Message]:
        return self.get(config.STM_LATEST_MESSAGES)

    def save(self, value: list[Message]) -> None:
        self._store.save(value)

    def append(self, value: Message) -> None:
        self._store.append(value)

    def remove(self, value: list[Message]) -> None:
        if not value:
            return
        remove_ids = {message.id for message in value}
        kept = [message for message in self.get() if message.id not in remove_ids]
        self.save(kept)

    @staticmethod
    def _format_short(messages: list[Message]) -> str:
        if not messages:
            return "(keine Nachrichten)"
        return "\n".join(message.text_short for message in messages)

    @staticmethod
    def _format_long(messages: list[Message]) -> str:
        if not messages:
            return "(keine Nachrichten)"
        return "\n".join(message.text_long for message in messages)

    @property
    def text_short_latest(self) -> str:
        return self._format_short(self.latest)

    @property
    def text_short(self) -> str:
        return self._format_short(self.get())

    @property
    def text_latest(self) -> str:
        return self._format_long(self.latest)

    @property
    def text(self) -> str:
        return self._format_long(self.get())

    def batch_messages(self) -> list[Message]:
        messages = self.get()
        messages_to_keep = config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP
        batch_size_threshold = config.UPDATER_ETM_BATCH_SIZE_THRESHOLD
        batch = messages[:-messages_to_keep] if messages_to_keep > 0 else list(messages)
        if len(batch) <= batch_size_threshold:
            return []
        return batch

    @property
    def batch_text_short(self) -> str:
        batch = self.batch_messages()
        if not batch:
            return ""
        return "\n".join(message.text_short for message in batch)


@dataclass(frozen=True)
class EtmNode:
    path: Path

    @property
    def sqlite(self) -> Path:
        return self.path

    @property
    def _store(self) -> _EtmSqliteStore:
        return _EtmSqliteStore(self.path)

    def append(self, text: str, embedding: list[float]) -> str:
        id = str(uuid4())
        self._store.append(
            id=id,
            text=text,
            embedding=embedding,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return id

    def delete(self, ids: list[str]) -> None:
        self._store.delete(ids)

    def get(self) -> list[Episode]:
        return self._store.get()


@dataclass(frozen=True)
class _StorageNodeBase:
    npc_id: str
    scene_id: str

    @property
    def runtime_dir(self) -> Path:
        return path_resolver.runtime_npc_scene_dir(self.npc_id, self.scene_id)


@dataclass
class SessionNode:
    path: Path

    @property
    def _yaml(self) -> YamlFile:
        return YamlFile(self.path)

    @property
    def _state(self) -> SessionState:
        return SessionState.model_validate(self._yaml.get() or {})

    def _save(self, state: SessionState) -> None:
        self._yaml.save(state.model_dump())

    @property
    def npc_id(self) -> str:
        return self._state.npc_id

    @npc_id.setter
    def npc_id(self, value: str) -> None:
        current = self._state
        self._save(SessionState(npc_id=value, scene_id=current.scene_id))

    @property
    def scene_id(self) -> str:
        return self._state.scene_id

    @scene_id.setter
    def scene_id(self, value: str) -> None:
        current = self._state
        self._save(SessionState(npc_id=current.npc_id, scene_id=value))


@dataclass(frozen=True)
class PromptsNode:
    @property
    def image_build(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("image_build_prompt.md"))

    @property
    def image_refresh(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("image_refresh.md"))

    @property
    def image_scene(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("image_scene.md"))

    @property
    def etm_update(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("etm_update.md"))

    @property
    def chat_general_rules(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("chat_general_rules.md"))

    @property
    def state_update(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("state_update.md"))

    @property
    def scene_update(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("scene_update.md"))


@dataclass(frozen=True)
class NpcNode(_StorageNodeBase):

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

    @property
    def description_original(self) -> TextFile:
        return TextFile(path_resolver.npc_original_file(self.npc_id, "description.md"))

    @property
    def description(self) -> TextFile:
        runtime_item = TextFile(self.base_runtime / "description.md")
        if runtime_item.is_file():
            return runtime_item
        return self.description_original

    @property
    def system_prompt_original(self) -> TextFile:
        return TextFile(path_resolver.npc_original_file(self.npc_id, "system_prompt.md"))

    @property
    def system_prompt(self) -> TextFile:
        return TextFile(path_resolver.npc_file(self.npc_id, self.scene_id, "system_prompt.md"))

    @property
    def character_original(self) -> YamlFile:
        return YamlFile(path_resolver.npc_original_file(self.npc_id, "character.yaml"))

    @property
    def character(self) -> YamlFile:
        return YamlFile(path_resolver.npc_file(self.npc_id, self.scene_id, "character.yaml"))

    @property
    def state_runtime(self) -> TextFile:
        return TextFile(self.base_runtime / "state.md")

    @property
    def state_original(self) -> TextFile:
        return TextFile(path_resolver.npc_original_file(self.npc_id, "state.md"))

    @property
    def state(self) -> str:
        runtime_item = self.state_runtime
        if runtime_item.is_file():
            return runtime_item.get()
        base_state = self.state_original.get().strip()
        relationship = self.relationship.get().strip()
        return "\n\n".join(part for part in (base_state, relationship) if part)

    @property
    def relationship_original(self) -> TextFile:
        return TextFile(path_resolver.npc_original_file(self.npc_id, "relationship.md"))

    @property
    def relationship(self) -> TextFile:
        return self.relationship_original

    @property
    def stm(self) -> StmNode:
        return StmNode(self.base_runtime / "stm.jsonl")

    @property
    def etm(self) -> EtmNode:
        return EtmNode(path=self.base_runtime / "etm.sqlite")

    @property
    def img_runtime(self) -> ImageFile:
        return ImageFile(self.base_runtime / "img.png")

    @property
    def img_original(self) -> ImageFile:
        return ImageFile(path_resolver.npc_original_file(self.npc_id, "img.png"))

    @property
    def img(self) -> ImageFile:
        runtime_img = self.img_runtime
        if runtime_img.is_file():
            return runtime_img
        scene_img = ImageFile(path_resolver.npc_scene_original_file(self.npc_id, self.scene_id, "img.png"))
        if scene_img.is_file():
            return scene_img
        return self.img_original

    @property
    def backup_dir(self) -> Path:
        return self.base_runtime / "img_backup"

    @property
    def orchestrator_dir(self) -> Path:
        return self.base_runtime / "orchestrator"

    def orchestrator_text(self, filename: str) -> TextFile:
        return TextFile(self.orchestrator_dir / filename)

    @property
    def image_prompt(self) -> TextFile:
        return TextFile(self.orchestrator_dir / "image_updater_update_prompt.txt")

@dataclass(frozen=True)
class SceneNode(_StorageNodeBase):

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

    @property
    def scene_runtime(self) -> TextFile:
        return TextFile(self.base_runtime / "scene.md")

    @property
    def scene_original(self) -> TextFile:
        return TextFile(path_resolver.scene_original_file(self.scene_id, "scene.md"))

    @property
    def scene(self) -> TextFile:
        return TextFile(path_resolver.scene_file(self.npc_id, self.scene_id, "scene.md"))

    @property
    def npc_scene_original(self) -> TextFile:
        return TextFile(path_resolver.npc_scene_original_file(self.npc_id, self.scene_id, "scene.md"))

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
    def img_original(self) -> ImageFile:
        return ImageFile(path_resolver.scene_original_file(self.scene_id, "img.png"))

    @property
    def img(self) -> Path:
        return self.img_original.get()

