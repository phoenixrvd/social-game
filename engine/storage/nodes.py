from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from engine.config import config
from engine.storage.files import ImageFile, TextFile, VideoFile, YamlFile
from engine.storage.models import Message, SessionState
from engine.storage.paths import path_resolver
from engine.storage.stores import _StmJsonlStore


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
        raw_state = self._yaml.get() or {}
        state = SessionState.model_validate(raw_state)
        normalized_state = state.model_dump()
        if raw_state != normalized_state:
            self._yaml.save(normalized_state)
        return state

    def _save(self, state: SessionState) -> None:
        self._yaml.save(SessionState.model_validate(state.model_dump()).model_dump())

    @property
    def npc_id(self) -> str:
        return self._state.npc_id

    @npc_id.setter
    def npc_id(self, value: str) -> None:
        self._save(self._state.model_copy(update={"npc_id": value}))

    @property
    def scene_id(self) -> str:
        return self._state.scene_id

    @scene_id.setter
    def scene_id(self, value: str) -> None:
        self._save(self._state.model_copy(update={"scene_id": value}))

    @property
    def image_autogenerate(self) -> bool:
        return self._state.image_autogenerate

    @image_autogenerate.setter
    def image_autogenerate(self, value: bool) -> None:
        self._save(self._state.model_copy(update={"image_autogenerate": value}))

    @property
    def scene(self) -> SceneNode:
        return SceneNode(npc_id=self.npc_id, scene_id=self.scene_id)


@dataclass(frozen=True)
class PromptsNode:
    @property
    def image_style_rules(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("image_style_rules.md"))

    @property
    def scene_create_image(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("scene_create_image.md"))

    @property
    def scene_create_text(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("scene_create_text.md"))

    @property
    def scene_describe_image(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("scene_describe_image.md"))

    @property
    def npc_create_description(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("npc_create_description.md"))

    @property
    def npc_create_state(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("npc_create_state.md"))

    @property
    def npc_create_image(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("npc_create_image.md"))

    @property
    def npc_create_image_from_reference(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("npc_create_image_from_reference.md"))

    @property
    def npc_describe_image(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("npc_describe_image.md"))

    @property
    def npc_scene_create_text(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("npc_scene_create_text.md"))

    @property
    def npc_scene_adapt_default_text(self) -> TextFile:
        return TextFile(path_resolver.prompt_file("npc_scene_adapt_default_text.md"))

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
    def override_base(self) -> Path:
        return config.OVERRIDES_NPC_DIR / self.npc_id

    @property
    def base_runtime(self) -> Path:
        return self.runtime_dir

    @property
    def default_base(self) -> Path:
        return config.NPC_DIR / config.DEFAULT_NPC_ID

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
        return self.state_original.get()

    @property
    def stm(self) -> StmNode:
        return StmNode(self.base_runtime / "stm.jsonl")

    @property
    def etm_dir(self) -> Path:
        return self.base_runtime / "etm_lightrag"

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
    def is_image_original(self) -> bool:
        return not self.img_runtime.is_file()

    @property
    def video(self) -> VideoFile:
        for video in self.video_candidates:
            if video.is_file():
                return video
        return self.video_default

    @property
    def video_override(self) -> VideoFile:
        return VideoFile(self.override_base / "video.mp4")

    @property
    def video_default(self) -> VideoFile:
        return VideoFile(config.NPC_DIR / self.npc_id / "video.mp4")

    @property
    def video_candidates(self) -> tuple[VideoFile, ...]:
        return (self.video_override, self.video_default)

    @property
    def backup_dir(self) -> Path:
        return self.base_runtime / "img_backup"

    @property
    def img_backup(self) -> list[ImageFile]:
        if not self.backup_dir.exists():
            return []

        backups = sorted(self.backup_dir.glob("img-*.png"), key=lambda path: path.name, reverse=True)
        return [ImageFile(path) for path in backups]

    @property
    def orchestrator_dir(self) -> Path:
        return self.base_runtime / "orchestrator"

    @property
    def image_prompt(self) -> TextFile:
        return TextFile(self.orchestrator_dir / "image_updater_update_prompt.txt")

    @property
    def user_profile_runtime(self) -> TextFile:
        return TextFile(self.base_runtime / "user_profile.md")

    @property
    def user_profile(self) -> str:
        preferred = path_resolver.preferred_file(path_resolver.user_profile_candidates(self.npc_id, self.scene_id))
        return TextFile(preferred).get() or ""

    @property
    def is_dynamic_npc(self) -> bool:
        is_default_npc = (config.NPC_DIR / self.npc_id).is_dir()
        is_override_npc = (config.OVERRIDES_NPC_DIR / self.npc_id).is_dir()
        return is_override_npc and not is_default_npc


@dataclass(frozen=True)
class SceneLocationNode(_StorageNodeBase):
    @property
    def runtime(self) -> TextFile:
        return TextFile(self.runtime_dir / "scene.md")

    @property
    def override(self) -> TextFile:
        return TextFile(config.OVERRIDES_SCENE_DIR / self.scene_id / "scene.md")

    @property
    def img_override(self) -> ImageFile:
        return ImageFile(config.OVERRIDES_SCENE_DIR / self.scene_id / "img.png")

    @property
    def original(self) -> TextFile:
        return TextFile(path_resolver.scene_original_file(self.scene_id, "scene.md"))

    @property
    def current(self) -> TextFile:
        return TextFile(path_resolver.scene_file(self.npc_id, self.scene_id, "scene.md"))

    @property
    def img_original(self) -> ImageFile:
        return ImageFile(path_resolver.scene_original_file(self.scene_id, "img.png"))

    @property
    def img(self) -> Path:
        return self.img_original.get()

    @property
    def is_dynamic(self) -> bool:
        is_default_scene = (config.SCENE_DIR / self.scene_id).is_dir()
        is_override_scene = (config.OVERRIDES_SCENE_DIR / self.scene_id).is_dir()
        return is_override_scene and not is_default_scene


@dataclass(frozen=True)
class NpcSceneContextNode(_StorageNodeBase):
    @property
    def original(self) -> TextFile:
        return TextFile(path_resolver.npc_scene_original_file(self.npc_id, self.scene_id, "scene.md"))

    @property
    def override(self) -> TextFile:
        return TextFile(config.OVERRIDES_NPC_DIR / self.npc_id / "scenes" / self.scene_id / "scene.md")

    @property
    def static(self) -> TextFile:
        return TextFile(config.NPC_DIR / self.npc_id / "scenes" / self.scene_id / "scene.md")

    @property
    def existing_file(self) -> TextFile | None:
        preferred = path_resolver.first_existing_file((self.override.path, self.static.path))
        return TextFile(preferred) if preferred is not None else None


@dataclass(frozen=True)
class SceneNode(_StorageNodeBase):
    @property
    def location(self) -> SceneLocationNode:
        return SceneLocationNode(npc_id=self.npc_id, scene_id=self.scene_id)

    @property
    def npc_context(self) -> NpcSceneContextNode:
        return NpcSceneContextNode(npc_id=self.npc_id, scene_id=self.scene_id)

    @property
    def description(self) -> str:
        runtime_scene = self.location.runtime
        if runtime_scene.is_file():
            return runtime_scene.get()
        description = self.location.original.get()
        npc_scene = self.npc_context.original
        if npc_scene.is_file():
            return "\n".join([description, npc_scene.get()])
        return description
