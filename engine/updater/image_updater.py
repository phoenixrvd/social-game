from __future__ import annotations

from engine.config import config
from engine.storage import storage
from engine.services.character_image_service import CharacterImageService
from engine.updater.updater import AbstractUpdater


class ImageUpdater(AbstractUpdater):
    def __init__(self) -> None:
        self.service = CharacterImageService()
        self.npc_store = self.service.npc_store

    def _run_trigger_item(self):
        npc = self.npc_store.load()
        npc_paths = storage.npc_view(npc_id=npc.npc_id, scene_id=npc.scene.scene_id)
        return npc_paths.orchestrator_text("image_updater_run.flag")

    def emit_update(self) -> None:
        self._run_trigger_item().save("1")

    def emit_update_if_missing(self) -> None:
        if self.service.has_generated_image():
            return

        self.emit_update()

    def _consume_run_toggle(self) -> bool:
        run_trigger_item = self._run_trigger_item()
        if not run_trigger_item.exists():
            return False

        run_trigger_item.path.unlink()
        return True

    @staticmethod
    def get_update_interval() -> int:
        return config.UPDATER_IMAGE_CHECK_INTERVAL_SECONDS

    def schedule(self, force: bool = False) -> None:
        if not self._consume_run_toggle():
            return

        self.service.update_from_context(force=force)
