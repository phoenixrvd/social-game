from __future__ import annotations

from engine.services.history_service import HistoryService
def create() -> None:
    """Speichert den aktuellen Zustand als Checkpoint."""

    HistoryService().save_checkpoint()


def checkpoints():
    """Liefert alle verfügbaren Checkpoints mit Metadaten."""

    return HistoryService().list_checkpoints()


def restore(commit_hash: str) -> None:
    """Stellt den Zustand aus einem gespeicherten Checkpoint wieder her."""

    HistoryService().restore_checkpoint(commit_hash)
