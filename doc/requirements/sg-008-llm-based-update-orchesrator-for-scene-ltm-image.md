# SG-008 - LLM-basierter Update-Orchestrator für Scene, State, LTM und Image

## Verbindlicher Stand

Diese Anforderung beschreibt den verbindlichen fachlichen Vertrag.

Wesentliche Leitplanken:

- Scope: `scene`, `state`, `ltm`, `image`
- Orchestrator-Start über Web-GUI-Start (`sg web`)
- kein LangGraph
- keine separaten Refresh-Services; Logik liegt in den Updater-Klassen
- Alle Updater führen ihren Prompt-Schritt direkt aus, sobald ihre Aktivierungsbedingungen erfüllt sind.
- Kostenfokus: unnötige LLM- und Bildmodell-Aufrufe werden über Aktivierungs-Gates vermieden

## Ziel

Ein leichter Orchestrator soll periodisch spezialisierte Updater ausführen:

- `scene`
- `state`
- `ltm`
- `image`

Die Aktivierung wird pro Updater innerhalb von `schedule()` entschieden.

## CLI-Vertrag

Verbindlicher Befehlssatz:

- `sg web`
- `sg session set --npc <npc_id> --scene <scene_id>`
- `sg update <ltm|scene|state|image>`
- `sg image-revert` (CLI-Command vorhanden; hängt von `ImageUpdater.revert()` ab)

### Orchestrator-Start

Der Watch-Loop startet beim Web-GUI-Start (`sg web`) einen `BackgroundScheduler` und registriert
für jeden Updater einen periodischen Job mit `updater.get_update_interval()`. Beim Start wird
`schedule()` zusätzlich einmalig direkt aufgerufen.

### Manueller Einzel-Run

- `sg update <ltm|scene|state|image>`

Führt `schedule()` des gewählten Updaters einmalig aus.

## Systemvertrag

### Updater-Interface

`AbstractUpdater` definiert zwei abstrakte Methoden:

- `get_update_interval() -> int`
- `schedule() -> None`

Konkrete Updater kapseln ihre Aktivierungslogik, Prompt-Erzeugung und Persistenz vollständig innerhalb von `schedule()`.

`schedule()` kapselt den vollständigen Update-Zyklus pro Updater intern.

### Orchestrator-Ablauf

`schedule()` implementiert pro Updater intern folgendes Muster:

1. Aktivierungsbedingungen prüfen -> bei `False` abbrechen
2. Prompt-Input erstellen
3. LLM-Aufruf ausführen
4. Ergebnis persistieren

Für `scene`, `state` und `ltm` wird die Aktivierung über neue Nachrichten seit dem letzten Check gesteuert. `image` verwendet stattdessen ein explizites Run-Flag, das ausschließlich von `SceneUpdater` und `StateUpdater` gesetzt wird.

Damit gilt verbindlich für Kosteneffizienz:

1. `ltm`, `scene`, `state` laufen nur, wenn seit dem letzten Check mindestens eine neue STM-Nachricht vorliegt.
2. `image` darf nur laufen, wenn zuvor `scene` oder `state` den Image-Run-Trigger gesetzt hat.
3. `image` erzeugt nur dann ein neues Bild, wenn der neu generierte Bildprompt gegenüber dem zuletzt gespeicherten Prompt als hinreichend verändert gilt.

Ausnahme: Der manuelle Web-Endpoint `/api/image/refresh-active` ruft `ImageUpdater.schedule(force=True)` auf und darf die Prompt-Differenz-Gates gezielt übersteuern.

### Registrierte Reihenfolge

Im Orchestrator-Lauf werden die Updater aktuell in dieser Reihenfolge registriert:

1. `LtmUpdater`
2. `SceneUpdater`
3. `StateUpdater`
4. `ImageUpdater`

Das ist relevant, weil `ImageUpdater` erst nach `scene` und `state` ausgeführt wird und von deren Run-Triggern profitieren kann.

## Persistenzprinzip

- Für jeden Updater wird ein persistenter Vergleichsstand geführt, damit neue Nachrichten seit dem letzten verarbeiteten Stand erkannt werden.
- Für den Bild-Workflow wird ein persistenter Trigger- und Prompt-Stand geführt, um unnötige Bildgenerierungen zu vermeiden.
- Bildaktualisierungen müssen den zuletzt gültigen Bildstand überschreibbar und wiederherstellbar halten (inklusive Backup-Mechanik).

## Updater-Übersicht

### SceneUpdater

- Aktivierung:
  - neue Nachrichten seit dem zuletzt verarbeiteten Stand
- Intervall:
  - `UPDATER_SCENE_CHECK_INTERVAL_SECONDS`
- Datenbasis für Prompt:
  - `prompts/scene_update.md`
  - aktuelle Szenenbeschreibung
  - letzte `STATE_AUTO_TRIGGER_LAST_N_MESSAGES` STM-Nachrichten
  - LTM
- Ausführung:
  - Persistenz über `NpcStore.save_scene(...)`
  - setzt danach den Run-Trigger für `ImageUpdater`
  - Hinweis: Der Trigger wird nach erfolgreichem Scene-Lauf gesetzt; es gibt aktuell keinen separaten Inhaltsvergleich "alter vs. neuer Scene-Text" vor dem Triggern.

### StateUpdater

- Aktivierung:
  - neue Nachrichten seit dem zuletzt verarbeiteten Stand
- Intervall:
  - `UPDATER_STATE_CHECK_INTERVAL_SECONDS`
- Datenbasis für Prompt:
  - `prompts/state_update.md`
  - aktueller State
  - STM
  - LTM
- Ausführung:
  - Persistenz über `NpcStore.save_state(...)`
  - setzt danach den Run-Trigger für `ImageUpdater`
  - Hinweis: Der Trigger wird nach erfolgreichem State-Lauf gesetzt; es gibt aktuell keinen separaten Inhaltsvergleich "alter vs. neuer State-Text" vor dem Triggern.

### LtmUpdater

- Aktivierung:
  - Batch `stm[:-UPDATER_LTM_SHORT_MEMORY_MESSAGES_TO_KEEP]` muss größer als `UPDATER_LTM_BATCH_SIZE_THRESHOLD` sein
  - neue Nachrichten seit dem zuletzt verarbeiteten Stand
- Intervall:
  - `UPDATER_LTM_CHECK_INTERVAL_SECONDS`
- Datenbasis:
  - aktuelle LTM
  - Kandidaten-Batch aus alten STM-Nachrichten
- Ausführung:
  1. Prompt aus `prompts/ltm_summary.md`
  2. Persistenz über `NpcStore.save_ltm(...)`
  3. verwendete STM-Nachrichten über `NpcStore.remove_stm_by_ids(...)` entfernen

### ImageUpdater

- Aktivierung:
  - ein expliziter Bild-Run-Trigger wurde gesetzt (durch `SceneUpdater` oder `StateUpdater`)
- Intervall:
  - `UPDATER_IMAGE_CHECK_INTERVAL_SECONDS`
- Datenbasis für Prompt:
  - `prompts/image_build_prompt.md`
  - bisheriger Bildprompt (oder leerer Startwert)
  - aktueller State
  - aktuelle Szene
- Ausführung:
  1. LLM erzeugt optimierten Bildprompt
  2. bei unverändertem Prompt: Skip (`image_skip`, Grund `prompt_unchanged_exact`)
  3. bei >95% Fuzzy-Ähnlichkeit: Skip (`prompt_similar_fuzzy`)
  4. bei >85% Token-Überlappung: Skip (`prompt_similar_tokens`)
  5. sonst: Bild über `refresh_img(...)` aktualisieren
  6. vorhandenes `img.png` vor dem Schreiben in Backup verschieben
  7. neuen Prompt und neues Bild persistieren

### Präzisierung "nur bei neuen Nachrichten"

- Die Nachrichtenerkennung basiert auf Zeitstempeln in `stm[*].timestamp_utc` und einem pro Updater persistent geführten Vergleichsstand.
- Es werden alle STM-Rollen (`user`, `assistant`, `system`) berücksichtigt; die Rollen werden aktuell nicht separat gewichtet.
- Wird kein neuer Zeitstempel gefunden, endet `schedule()` ohne Prompt-Start und ohne Persistenz.
- Der jeweilige `last_check` wird beim Gate-Pass sofort aktualisiert (vor dem LLM-Call). Bei Fehlern im folgenden Prompt-/Persistenzschritt gibt es daher ohne neue Nachrichten keinen automatischen Retry.

