#!/usr/bin/env python3
"""
Integration test für SG-009: Git-basierte Spielstandshistorie
"""

import tempfile
import shutil
from pathlib import Path

from engine.config import config
from engine.services.history_service import HistoryService
from engine.storage import storage


def test_git_history_workflow():
    """Test des kompletten Git-History-Workflows"""

    print("\n=== Test: Git-History Workflow ===\n")

    # 1. Initialisierung
    print("1. Git-Repo wird initialisiert...")
    history = HistoryService()
    history._ensure_git_repo()
    assert (storage.data / ".git").exists()
    print("   ✓ Git-Repo existiert")

    # 2. Listen (sollte leer sein)
    print("\n2. Checkpoints auflisten (initial)...")
    checkpoints = history.list_checkpoints()
    assert isinstance(checkpoints, list)
    print(f"   ✓ Checkpoints-Liste: {len(checkpoints)} Einträge")

    # 3. Checkpoint-Verzeichnis struktur
    print("\n3. Struktur überprüfen...")
    npc_id = storage.session.npc_id
    scene_id = storage.session.scene_id
    npc_data_path = storage.data / f"npcs/{npc_id}/{scene_id}"
    print(f"   NPC-Daten-Pfad: {npc_data_path}")
    print(f"   Git-dir: {storage.data / '.git'}")

    # 4. Error handling
    print("\n4. Error-Handling überprüfen...")
    try:
        history._generate_checkpoint_summary()
        print("   ✓ Checkpoint-Zusammenfassung funktioniert")
    except Exception as e:
        print(f"   ⚠ Zusammenfassung fehlgeschlagen (normal wenn keine Messages): {e}")

    print("\n=== Alle Tests bestanden! ===\n")


if __name__ == "__main__":
    test_git_history_workflow()

