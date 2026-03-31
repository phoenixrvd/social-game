---
state: implemented
---

# SG-002: Long-Term-Memory

Das System soll eine Long-Term-Memory besitzen, um den Kontext eines laufenden Dialogs zu speichern und darauf basierend konsistente Antworten zu generieren.

## Technische Details

- Das Memory ist technisch eine Zusammenfassung aus dem letzten LTM-Zustand und Nachrichten aus dem Short-Memory.
- Die Quelle für die Zusammenfassung ist ausschließlich das Short-Memory.
- Die Regeln für die Zusammenfassung sind ein Single-Shot-Prompt unter `prompts/ltm_summary.md`.
- Für die Zusammenfassung wird dasselbe Modell genommen wie für die Dialoge (siehe [ADR-004](../adr/004-modellstrategie.md)).
- LTM-Updates werden über den periodischen Orchestrator-Lauf der Web-GUI sowie manuell über `sg update ltm` angestoßen.
- Die Aktivierungslogik des LTM-Updaters:
  - STM enthält mehr als `UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP = 20` Nachrichten,
  - neue Nachrichten seit dem letzten Check vorhanden.
- Das Intervall `UPDATER_LTM_CHECK_INTERVAL_SECONDS` steuert den Scheduler-Takt des Jobs, nicht eine zusätzliche Laufzeit-Gate-Bedingung innerhalb von `schedule()`.
- Als Kandidaten-Batch werden alle STM-Nachrichten außer den letzten `UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP = 20` verwendet.
- Reihenfolge beim Update:
  - LTM mit den ausgewählten Short-Memory-Nachrichten aktualisieren,
  - LTM speichern,
  - danach genau diese verarbeiteten Nachrichten aus dem Short-Memory entfernen (Aufmerksamkeitseffekt).
- Persistenz ist pro NPC dauerhaft und szenenkonsistent verfügbar, damit der Langzeitkontext über mehrere Turns erhalten bleibt.
- Im Laufzeitmodell ist die Long-Term-Memory eine Eigenschaft des `Npc`-Objekts (`Npc.ltm`) und wird über `NpcStore` geladen/gespeichert.
- Token-Budget:
  - Zielgröße ca. 1200-1800 Tokens,
  - harte Obergrenze ca. 2200 Tokens,
  - bei Überschreitung wird erneut verdichtet.
- Fehlerverhalten (PoC): Wenn der LTM-Update fehlschlägt, darf der Prozess abbrechen (kein stilles Fallback).
- Manuell auslösbar per `sg update ltm`, das `schedule()` aufruft und bei erfüllten Aktivierungsbedingungen den LTM-Update-Zyklus vollständig ausführt.

