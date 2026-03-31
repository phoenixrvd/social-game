---
state: implemented
---

# SG-003: Short-Term-Memory

Das System soll ein Short-Term-Memory besitzen, um den Kontext eines laufenden Dialogs zu speichern und darauf basierend konsistente Antworten zu generieren.

## Technische Details

- Das Short-Term-Memory (STM) ist die persistierte Konversationsgeschichte pro NPC.
- Persistenzort: `.data/npcs/<npc_id>/stm.jsonl`.
- Beim Start eines Dialogs wird das STM fuer den NPC geladen.
- Pro Dialog-Turn werden genau diese Nachrichten in das STM geschrieben:
  - die neue `user`-Nachricht,
  - die neue `assistant`-Antwort.
- Die Reihenfolge im STM bleibt strikt chronologisch.
- Das STM ist die einzige Quelle fuer SG-002 (LTM-Zusammenfassung).
- Wenn SG-002 ein Batch erfolgreich verarbeitet hat, werden genau diese verarbeiteten Nachrichten aus dem STM entfernt.
- Das STM darf den Dialogfluss nicht blockieren; Speicheroperationen muessen leichtgewichtig bleiben.
- Wird das Laufzeitverzeichnis `.data/npcs/<npc_id>` fuer einen NPC geloescht (Reset), gilt dessen STM als vollstaendig zurueckgesetzt.

## Akzeptanzkriterien

- Nach Neustart des Programms wird das zuvor gespeicherte STM fuer denselben NPC wieder geladen.
- Nach einem erfolgreichen Dialog-Turn sind genau 2 neue Nachrichten im STM vorhanden (`user`, `assistant`).
- Nach einem erfolgreichen SG-002-Update sind die verarbeiteten Nachrichten nicht mehr im STM vorhanden.
- Nach einer Dialogpfad-Loeschung im Chat enthaelt das STM keine Nachricht mehr ab dem ausgewaehlten Loeschpunkt.
- Nach einem NPC-Reset ueber die Web-GUI enthaelt `.data/npcs/<npc_id>/stm.jsonl` keine vorherigen Dialognachrichten mehr.
- Die verbleibenden Nachrichten sind weiterhin in korrekter zeitlicher Reihenfolge.

