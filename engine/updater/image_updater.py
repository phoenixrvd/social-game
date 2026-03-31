from __future__ import annotations
from rapidfuzz import fuzz

from datetime import UTC, datetime
from pathlib import Path

from engine.logging import get_logger, log_info
from engine.config import config
from engine.fs_utils import load_text, save_text
from engine.llm_client import refresh_img, run_prompt_small
from engine.stores.npc_store import NpcStore
from engine.updater.updater import AbstractUpdater

BUILD_IMAGE_PROMPT_PATH = config.PROJECT_ROOT / "prompts" / "image_build_prompt.md"

IMAGE_RUN_TRIGGER_FILENAME = "image_updater_run.flag"
IMAGE_NAME = "img.png"
IMAGE_PROMPT_FILENAME = "image_updater_update_prompt.txt"
IMAGE_LAST_ERROR_FILENAME = "image_updater_last_error.txt"
BACKUP_DIR_NAME = "img_backup"
BACKUP_GLOB = "img-*.png"
BACKUP_TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"
LOGGER = get_logger("updater.image")


class ImageUpdater(AbstractUpdater):

    def __init__(self) -> None:
        self.npc_store = NpcStore()

    def _run_trigger_path(self) -> Path:
        return self._orchestrator_dir() / IMAGE_RUN_TRIGGER_FILENAME

    def emit_update(self) -> None:
        save_text(self._run_trigger_path(), "1")

    def _consume_run_toggle(self) -> bool:
        run_trigger_path = self._run_trigger_path()
        if not run_trigger_path.exists():
            return False

        run_trigger_path.unlink()
        return True

    def _image_path(self) -> Path:
        return self._current_npc_scene_data_dir() / IMAGE_NAME

    def _backup_dir(self) -> Path:
        return self._current_npc_scene_data_dir() / BACKUP_DIR_NAME

    def _image_prompt_path(self) -> Path:
        return self._orchestrator_dir() / IMAGE_PROMPT_FILENAME

    def _last_error_path(self) -> Path:
        return self._orchestrator_dir() / IMAGE_LAST_ERROR_FILENAME

    def get_last_error(self) -> str:
        return load_text(self._last_error_path()).strip()

    def _save_last_error(self, message: str) -> None:
        save_text(self._last_error_path(), message.strip())

    def _clear_last_error(self) -> None:
        path = self._last_error_path()
        if path.exists():
            path.unlink()

    def _latest_backup_path(self) -> Path | None:
        backup_dir = self._backup_dir()
        if not backup_dir.exists():
            return None

        backups = sorted(backup_dir.glob(BACKUP_GLOB))
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
        backup_path = backup_dir / f"img-{datetime.now(UTC).strftime(BACKUP_TIMESTAMP_FORMAT)}.png"
        image_path.rename(backup_path)
        log_info(LOGGER, "image_backup_created", source=image_path, backup=backup_path)

    def _load_old_prompt(self) -> str:
        prompt_path = self._image_prompt_path()
        if not prompt_path.exists():
            return ""

        return load_text(prompt_path).strip()

    def get_preview(self, old_prompt: str) -> str:
        npc = self.npc_store.load()
        return (
            load_text(BUILD_IMAGE_PROMPT_PATH).strip()
            .replace("{{NPC_DESCRIPTION}}", npc.description)
            .replace("{{CURRENT_IMAGE_PROMPT}}", old_prompt or "(none)")
            .replace("{{CURRENT_STATE}}", npc.state)
            .replace("{{CURRENT_SCENE}}", npc.scene.description)
            .replace("{{CURRENT_STM}}", self.format_short_memory(npc.stm, last_n=config.UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP))
        )

    def _token_overlap(self, a: str, b: str) -> float:
        a_tokens = {t.strip() for t in a.split(",") if t.strip()}
        b_tokens = {t.strip() for t in b.split(",") if t.strip()}

        if not a_tokens:
            return 0.0

        return len(a_tokens & b_tokens) / len(a_tokens)

    def schedule(self, force: bool = False) -> None:
        if not self._consume_run_toggle():
            log_info(LOGGER, "updater_active", updater="image", active=False, prompt_start=False, reason="no_run_toggle_emitted")
            return

        log_info(LOGGER, "updater_active", updater="image", active=True, prompt_start=True)

        npc = self.npc_store.load()
        image_path = self._image_path()
        prompt_path = self._image_prompt_path()
        old_prompt = self._load_old_prompt().strip()

        optimization_prompt = self.get_preview(old_prompt)

        try:
            new_prompt = run_prompt_small(optimization_prompt).strip()
        except Exception as exc:
            self._save_last_error(str(exc))
            log_info(LOGGER, "image_update_failed", error=str(exc))
            raise

        # --- Hard check ---
        if new_prompt == old_prompt and not force:
            log_info(LOGGER, "image_skip", reason="prompt_unchanged_exact")
            return

        # --- Fuzzy similarity ---
        similarity = fuzz.ratio(new_prompt, old_prompt) / 100

        if similarity > 0.95 and not force: # stop if similar to X%
            log_info(LOGGER, "image_skip", reason="prompt_similar_fuzzy", similarity=similarity)
            return

        # --- Token overlap ---
        overlap = self._token_overlap(new_prompt, old_prompt)

        if overlap > 0.85 and not force: # stop if overlap to X%
            log_info(LOGGER, "image_skip", reason="prompt_similar_tokens", overlap=overlap)
            return

        # --- Generate image ---
        log_info(LOGGER, "image_generation_prompt", prompt=new_prompt)
        log_info(LOGGER, "image_generation_started", source_image=npc.img, target_image=image_path)

        try:
            new_img = refresh_img(new_prompt, npc.img.read_bytes())
        except Exception as exc:
            self._save_last_error(str(exc))
            log_info(LOGGER, "image_update_failed", error=str(exc))
            raise

        self._backup_existing_image(image_path)

        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(new_img)
        save_text(prompt_path, new_prompt)
        self._clear_last_error()

        log_info(LOGGER, "image_updated", path=image_path)
        log_info(LOGGER, "updater_completed", updater="image", prompt_length=len(new_prompt), image_bytes=len(new_img))

    def revert(self) -> tuple[str, bool]:
        npc = self.npc_store.load()
        image_path = self._image_path()
        backup_path = self._latest_backup_path()

        if not image_path.exists() and backup_path is None:
            return f"Kein Daten-Bild vorhanden fuer '{npc.npc_id}'.", False

        log_info(LOGGER, "image_revert_started", target=image_path, backup=backup_path)

        lines: list[str] = []

        if image_path.exists():
            image_path.unlink()
            lines.append("Bild geloescht.")

        if backup_path is None:
            lines.append("Kein Backup gefunden.")
            log_info(LOGGER, "image_revert_completed", revert=False, target_image=image_path, restored_from=None)
            return "\n".join(lines), False

        image_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.replace(image_path)
        lines.append(f"Backup wiederhergestellt: {backup_path} -> {image_path}")

        log_info(LOGGER, "image_revert_completed", revert=True, target_image=image_path, restored_from=backup_path)
        return "\n".join(lines), True

