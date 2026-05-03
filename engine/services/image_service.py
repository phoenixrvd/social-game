from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from rapidfuzz import fuzz

from engine.client import client
from engine.storage import storage
from engine.storage.files import ImageFile
from engine.storage.nodes import NpcNode, SceneNode


class ImageService:
    def has_generated_image(self) -> bool:
        return storage.npc.img_runtime.exists()

    def update_from_context(self, force: bool = False) -> None:
        npc = storage.npc
        scene = storage.scene
        image_path = npc.img_runtime

        if not image_path.exists() and self._has_scene_merge_prompt():
            self.merge_with_scene()
            return

        old_prompt = self._load_current_prompt(npc)
        new_prompt = self._generate_update_prompt(npc=npc, scene=scene, old_prompt=old_prompt)

        if self._should_skip_prompt_update(new_prompt, old_prompt, force):
            return

        self._refresh_from_prompt(npc=npc, image_path=image_path, new_prompt=new_prompt)

    def get_preview(
        self,
        old_prompt: str,
        npc: NpcNode | None = None,
        scene: SceneNode | None = None,
    ) -> str:
        current_npc = npc or storage.npc
        current_scene = scene or storage.scene
        return (
            storage.prompts.image_build.get().strip()
            .replace("{{NPC_DESCRIPTION}}", current_npc.description.get())
            .replace("{{CURRENT_IMAGE_PROMPT}}", old_prompt or "(none)")
            .replace("{{CURRENT_STATE}}", current_npc.state)
            .replace("{{CURRENT_SCENE}}", current_scene.description)
            .replace("{{CURRENT_STM}}", current_npc.stm.text_short_latest)
        )

    def merge_with_scene(self) -> None:
        current_npc = storage.npc
        current_scene = storage.scene
        image_path = current_npc.img_runtime
        prompt = self._scene_merge_prompt(current_scene.description)

        merged_img = client.merge_character_scene_img(
            prompt,
            current_npc.img.get().read_bytes(),
            current_scene.img.read_bytes(),
        )

        self._write_image(image_path, current_npc.backup_dir, merged_img)
        new_prompt = self._generate_update_prompt(npc=current_npc, scene=current_scene, old_prompt="")
        current_npc.image_prompt.save(new_prompt)

    def revert(self) -> None:
        npc = storage.npc
        image_path = npc.img_runtime.path
        backup_path = self._latest_backup_path(npc.backup_dir)

        if not image_path.exists() and backup_path is None:
            return

        if image_path.exists():
            image_path.unlink()

        if backup_path is None:
            return

        image_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.replace(image_path)

    def delete_current(self) -> None:
        image_path = storage.npc.img_runtime.path
        if not image_path.exists():
            return
        image_path.unlink()

    def _refresh_from_prompt(self, npc: NpcNode, image_path: ImageFile, new_prompt: str) -> None:
        new_img = client.refresh_img(
            self._render_refresh_prompt(new_prompt),
            npc.img.get().read_bytes(),
            npc.img_original.get().read_bytes(),
        )
        self._write_image(image_path, npc.backup_dir, new_img)
        npc.image_prompt.save(new_prompt)

    @staticmethod
    def _backup_existing_image(image_path: ImageFile, backup_dir: Path) -> None:
        if not image_path.exists():
            return

        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"img-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.png"
        image_path.path.rename(backup_path)

    @staticmethod
    def _load_current_prompt(npc: NpcNode) -> str:
        prompt_item = npc.image_prompt
        if not prompt_item.exists():
            return ""
        return prompt_item.get().strip()

    @staticmethod
    def _scene_merge_prompt(scene_description: str) -> str:
        return (
            storage.prompts.image_scene.get()
            .strip()
            .replace("{{SCENE_DESCRIPTION}}", scene_description)
        )

    @staticmethod
    def _has_scene_merge_prompt() -> bool:
        return bool(storage.prompts.image_scene.get().strip())

    @staticmethod
    def _render_refresh_prompt(base_prompt: str) -> str:
        return (
            storage.prompts.image_refresh.get()
            .strip()
            .replace("{{BASE_PROMPT}}", base_prompt.strip())
        )

    def _write_image(self, image_path: ImageFile, backup_dir: Path, image_bytes: bytes) -> None:
        self._backup_existing_image(image_path, backup_dir)
        image_path.save(image_bytes)

    def _generate_update_prompt(self, npc: NpcNode, scene: SceneNode, old_prompt: str) -> str:
        optimization_prompt = self.get_preview(old_prompt, npc=npc, scene=scene)
        return client.run_prompt_small(optimization_prompt).strip()

    @staticmethod
    def _token_overlap(a: str, b: str) -> float:
        a_tokens = {t.strip() for t in a.split(",") if t.strip()}
        b_tokens = {t.strip() for t in b.split(",") if t.strip()}
        if not a_tokens:
            return 0.0
        return len(a_tokens & b_tokens) / len(a_tokens)

    def _should_skip_prompt_update(self, new_prompt: str, old_prompt: str, force: bool) -> bool:
        if force:
            return False
        if new_prompt == old_prompt:
            return True
        if fuzz.ratio(new_prompt, old_prompt) / 100 > 0.95:
            return True
        return self._token_overlap(new_prompt, old_prompt) > 0.85

    @staticmethod
    def _latest_backup_path(backup_dir: Path) -> Path | None:
        if not backup_dir.exists():
            return None

        backups = sorted(backup_dir.glob("img-*.png"), key=lambda path: path.name)
        if not backups:
            return None
        return backups[-1]
