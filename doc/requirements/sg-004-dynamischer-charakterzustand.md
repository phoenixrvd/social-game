---
state: implemented
---

# SG-004: Dynamischer Charakterzustand

Der Charakterzustand wird dynamisch aktualisiert, um die Reaktionen der NPCs auf die Interaktionen des Spielers zu beeinflussen.

## Technische Details

- Der Charakterzustand wird synchron aktualisiert (siehe [ADR-003](../adr/003-synchroner-update-orchestrator.md)).
- Die Aktualisierung basiert auf `state.md` (alter Zustand), Short-Term-Memory und Long-Term-Memory.
- State-Updates werden über den periodischen Orchestrator-Lauf der Web-GUI sowie manuell über `sg update state` angestoßen.
- `sg update state` ruft `schedule()` auf und führt den State-Update-Zyklus bei erfüllten Aktivierungsbedingungen vollständig aus.
- Aktivierungsbedingung für einen State-Lauf: Es liegt mindestens eine neue STM-Nachricht seit dem zuletzt verarbeiteten State-Stand vor.
- Nach einem erfolgreichen State-Lauf wird der Bild-Run-Trigger für den `ImageUpdater` gesetzt.
- Der aktuelle State wird im Dialogkontext direkt im gemeinsamen Chat-Systemprompt berücksichtigt; es gibt keine separate zusätzliche Runtime-Systemnachricht mehr pro Turn.

