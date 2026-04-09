from __future__ import annotations
from rapidfuzz import fuzz

from datetime import UTC, datetime
from pathlib import Path

from engine.logging import get_logger, log_info
from engine.config import config
from engine.fs_utils import load_text, save_text
from engine.llm_client import merge_character_scene_img, refresh_img, run_prompt
from engine.stores.npc_store import NpcStore
from engine.updater.updater import AbstractUpdater

LOGGER = get_logger("updater.image")


class ImageUpdater(AbstractUpdater):

    def __init__(self) -> None:
        self.npc_store = NpcStore()

    def _run_trigger_path(self) -> Path:
        return self._orchestrator_dir() / "image_updater_run.flag"

    def emit_update(self) -> None:
        save_text(self._run_trigger_path(), "1")

    def emit_update_if_missing(self) -> None:
        if self.has_generated_image():
            return

        self.emit_update()

    def _consume_run_toggle(self) -> bool:
        run_trigger_path = self._run_trigger_path()
        if not run_trigger_path.exists():
            return False

        run_trigger_path.unlink()
        return True

    def _image_path(self) -> Path:
        return self._current_npc_scene_data_dir() / "img.png"

    def _backup_dir(self) -> Path:
        return self._current_npc_scene_data_dir() / "img_backup"

    def _image_prompt_path(self) -> Path:
        return self._orchestrator_dir() / "image_updater_update_prompt.txt"

    def has_generated_image(self) -> bool:
        return self._image_path().exists()

    @staticmethod
    def _load_optional_text(path: Path) -> str:
        if not path.exists():
            return ""

        return load_text(path).strip()

    def _latest_backup_path(self) -> Path | None:
        backup_dir = self._backup_dir()
        if not backup_dir.exists():
            return None

        backups = sorted(backup_dir.glob("img-*.png"))
        if not backups:
            return None

        return backups[-1]

    def get_update_interval(self) -> int:
        return config.UPDATER_IMAGE_CHECK_INTERVAL_SECONDS

    def _backup_existing_image(self, image_path: Path) -> None:
        if not image_path.exists():
            return

        backup_dir = self._backup_dir()
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"img-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.png"
        image_path.rename(backup_path)
        log_info(LOGGER, "image_backup_created", source=image_path, backup=backup_path)

    def _load_current_prompt(self) -> str:
        return self._load_optional_text(self._image_prompt_path())

    def _scene_merge_prompt(self, scene_description: str) -> str:
        return (
            load_text(config.PROJECT_ROOT / "prompts" / "image_scene.md")
            .strip()
            .replace("{{SCENE_DESCRIPTION}}", scene_description)
        )

    def _render_refresh_prompt(self, base_prompt: str) -> str:
        return (
            load_text(config.PROJECT_ROOT / "prompts" / "image_refresh.md")
            .strip()
            .replace("{{BASE_PROMPT}}", base_prompt.strip())
        )

    def _write_image(self, image_path: Path, image_bytes: bytes) -> None:
        self._backup_existing_image(image_path)
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(image_bytes)

    def get_preview(self, old_prompt: str) -> str:
        npc = self.npc_store.load()
        return (
            load_text(config.PROJECT_ROOT / "prompts" / "image_build_prompt.md").strip()
            .replace("{{NPC_DESCRIPTION}}", npc.description)
            .replace("{{CURRENT_IMAGE_PROMPT}}", old_prompt or "(none)")
            .replace("{{CURRENT_STATE}}", npc.state)
            .replace("{{CURRENT_SCENE}}", npc.scene.description)
            .replace("{{CURRENT_STM}}", self.format_short_memory(npc.stm, last_n=config.UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP))
        )

    def _generate_update_prompt(self, old_prompt: str) -> str:
        optimization_prompt = self.get_preview(old_prompt)
        return run_prompt(optimization_prompt, model=config.MODEL_LLM_SMALL).strip()

    def _token_overlap(self, a: str, b: str) -> float:
        a_tokens = {t.strip() for t in a.split(",") if t.strip()}
        b_tokens = {t.strip() for t in b.split(",") if t.strip()}

        if not a_tokens:
            return 0.0

        return len(a_tokens & b_tokens) / len(a_tokens)

    def _should_skip_prompt_update(self, new_prompt: str, old_prompt: str, force: bool) -> bool:
        if force:
            return False

        if new_prompt == old_prompt:
            log_info(LOGGER, "image_skip", reason="prompt_unchanged_exact")
            return True

        similarity = fuzz.ratio(new_prompt, old_prompt) / 100
        if similarity > 0.95:  # stop if similar to 95%
            log_info(LOGGER, "image_skip", reason="prompt_similar_fuzzy", similarity=similarity)
            return True

        overlap = self._token_overlap(new_prompt, old_prompt)
        if overlap > 0.85:  # stop if overlap is above 85%
            log_info(LOGGER, "image_skip", reason="prompt_similar_tokens", overlap=overlap)
            return True

        return False

    def schedule(self, force: bool = False) -> None:
        if not self._consume_run_toggle():
            log_info(LOGGER, "updater_active", updater="image", active=False, prompt_start=False, reason="no_run_toggle_emitted")
            return

        log_info(LOGGER, "updater_active", updater="image", active=True, prompt_start=True)

        image_path = self._image_path()

        if not image_path.exists():
            self.merge_with_scene()
            return

        npc = self.npc_store.load()
        prompt_path = self._image_prompt_path()
        old_prompt = self._load_current_prompt()
        new_prompt = self._generate_update_prompt(old_prompt)

        if self._should_skip_prompt_update(new_prompt, old_prompt, force):
            return

        log_info(LOGGER, "image_generation_prompt", prompt=new_prompt)
        log_info(
            LOGGER,
            "image_generation_started",
            source_image=npc.img_current,
            identity_image=npc.img,
            target_image=image_path,
        )

        new_img = refresh_img(
            self._render_refresh_prompt(new_prompt),
            npc.img_current.read_bytes(),
            npc.img.read_bytes(),
        )

        self._write_image(image_path, new_img)
        save_text(prompt_path, new_prompt)

        log_info(LOGGER, "image_updated", path=image_path)
        log_info(LOGGER, "updater_completed", updater="image", prompt_length=len(new_prompt), image_bytes=len(new_img))

    def refresh_image_with_current_prompt(self) -> None:
        """Regeneriert das Bild mit dem bestehenden Prompt, ohne ihn zu aktualisieren."""
        npc = self.npc_store.load()
        image_path = self._image_path()
        current_prompt = self._load_current_prompt()

        if not current_prompt:
            return

        log_info(LOGGER, "image_refresh_started", npc=npc.npc_id, prompt_length=len(current_prompt))

        new_img = refresh_img(
            self._render_refresh_prompt(current_prompt),
            npc.img_current.read_bytes(),
            npc.img.read_bytes(),
        )

        self._write_image(image_path, new_img)

        log_info(LOGGER, "image_refreshed", path=image_path, image_bytes=len(new_img))

    def merge_with_scene(self) -> None:
        npc = self.npc_store.load()
        image_path = self._image_path()
        prompt_path = self._image_prompt_path()
        prompt = self._scene_merge_prompt(npc.scene.description)

        log_info(LOGGER, "image_merge_started", source_image=npc.img_current, scene_image=npc.scene.img, target_image=image_path)

        merged_img = merge_character_scene_img(
            prompt,
            npc.img_current.read_bytes(),
            npc.scene.img.read_bytes(),
        )

        self._write_image(image_path, merged_img)
        save_text(prompt_path, self._generate_update_prompt(""))

        log_info(LOGGER, "image_merged_with_scene", path=image_path, image_bytes=len(merged_img))

    def revert(self) -> None:
        image_path = self._image_path()
        backup_path = self._latest_backup_path()

        if not image_path.exists() and backup_path is None:
            return

        log_info(LOGGER, "image_revert_started", target=image_path, backup=backup_path)

        if image_path.exists():
            image_path.unlink()

        if backup_path is None:
            log_info(LOGGER, "image_revert_completed", revert=False, target_image=image_path, restored_from=None)
            return

        image_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.replace(image_path)

        log_info(LOGGER, "image_revert_completed", revert=True, target_image=image_path, restored_from=backup_path)
