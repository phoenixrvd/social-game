---
state: implemented
---

# SG-006: Dynamischer Scene-State

Die Szene soll sich während eines laufenden Gesprächs dynamisch aktualisieren können, damit Umwelt und Aufenthaltsort konsistent mit dem Dialogverlauf bleiben.

## Technische Details

- Der Scene-State wird synchron aktualisiert (analog zu [ADR-003](../adr/003-synchroner-update-orchestrator.md)).
- Der Scene-State wird aus Dialogverlauf, Short-Term-Memory und Long-Term-Memory abgeleitet.
- Die Szene wird als eine Datei mit zwei Bereichen behandelt:
  - YAML Meta-Block (Scene-State),
  - Szenenbeschreibung als Markdown-Text.
- Das `Scene`-Modell enthält nur noch `scene_id` und die komplette Szenenbeschreibung in `description`; es gibt kein separates `state`- oder `config`-Feld mehr.
- Beim Persistieren eines Scene-Updates wird die komplette Szenendatei (Meta-Block + Beschreibung) aktualisiert.
- Der Prompt für Scene-Updates wird aus `prompts/scene_update.md` geladen und ist die normative Quelle für Ausgabeformat und Aktualisierungslogik.
- Scene-Updates werden über den periodischen Orchestrator-Lauf der Web-GUI sowie manuell über `sg update scene` angestoßen.
- Nach einem Scene-Update wird der aktuelle Scene-Stand im nächsten Turn direkt im gemeinsamen Chat-Systemprompt berücksichtigt.
- Manuell auslösbar per `sg update scene`, das `schedule()` aufruft und bei erfüllten Aktivierungsbedingungen den Scene-Update-Zyklus vollständig ausführt.
- `sg update scene` umgeht keine Auto-Gates; Aktivierungsbedingungen werden regulär geprüft.
- Aktivierungsbedingung für einen Scene-Lauf: Es liegt mindestens eine neue STM-Nachricht seit dem zuletzt verarbeiteten Scene-Stand vor.
- Nach einem erfolgreichen Scene-Lauf wird der Bild-Run-Trigger für den `ImageUpdater` gesetzt.

### Szenenbeschreibung: Aufbau aus globaler und NPC-spezifischer Quelle

Die aktive Szenenbeschreibung wird aus bis zu drei Quellen zusammengesetzt (erste vorhandene Laufzeitdatei gewinnt über alles):

1. **Laufzeitbeschreibung** (`.data/npcs/<npc_id>/<scene_id>/scene.md`) – vollständig vom Orchestrator geschriebene Szenendatei; wenn vorhanden, wird nur diese verwendet.
2. Falls keine Laufzeitdatei existiert, wird die Basisbeschreibung aus folgenden Quellen zusammengeführt:
   - **Globale Szenenbeschreibung** (`scenes/<scene_id>/scene.md`) – szenenübergreifende Grundlage.
   - **NPC-spezifische Szenenergänzung** (`npcs/<npc_id>/scenes/<scene_id>/scene.md`) – optionale, NPC-individuelle Ergänzung, die an die globale Beschreibung angehängt wird.

Damit können NPCs eine szenenspezifische Ausgangslage besitzen, ohne die globale Szenenbeschreibung zu überschreiben.

## Akzeptanzkriterien

- SG-006 gilt als erfüllt, wenn alle oben genannten technischen Punkte umgesetzt sind.
- Die Szenenbeschreibung wird korrekt aus globaler und NPC-spezifischer Quelle zusammengesetzt, wenn keine Laufzeitdatei vorhanden ist.
- Eine vorhandene Laufzeitbeschreibung (`.data/npcs/<npc_id>/<scene_id>/scene.md`) hat immer Vorrang vor der statischen Zusammenführung.


