---
state: implemented
---

# SG-010: Anwendungslogging

Das System soll ein zentrales Anwendungslogging bereitstellen, damit Chat-, Updater- und Bild-Workflows in einer gemeinsamen Logdatei nachvollziehbar sind.

## Technische Details

### Logziel

- Alle Anwendungslogs werden in `.data/app.log` geschrieben.
- Die Logdatei wird bei Bedarf automatisch angelegt.
- Das Logging verwendet einen zentral konfigurierten File-Logger.

### Log-Level

- Die in dieser Anforderung beschriebenen Ereignisse werden auf `INFO` geloggt.
- Das Format soll Zeitstempel, Log-Level, Logger-Namen und die Lognachricht enthalten.
- Fachliche Lognachrichten sollen als strukturierte Dict-/JSON-Objekte ausgegeben werden, nicht als frei formatierte Fliesstexte.
- Strukturierte Logeintraege sollen lesbar mehrzeilig mit Einrueckung im Log erscheinen.

### Chat-Logging

- Fuer Chat-Streams wird die Token-Nutzung geloggt.
- Das Logging enthaelt mindestens Prompt-Tokens, Completion-Tokens und Total-Tokens, sofern diese vom LLM-Provider geliefert werden.
- Falls keine Usage-Daten geliefert werden, wird dies ebenfalls als INFO-Ereignis festgehalten.
- Das Chat-Logging soll als strukturiertes Event mit klaren Feldern wie `event`, `prompt_tokens`, `completion_tokens`, `total_tokens` und `message_count` erscheinen.

### Updater-Logging

Fuer alle Updater (`ltm`, `scene`, `state`, `image`) wird geloggt:

- ob der Updater aktiv ist oder nicht,
- warum ein Updater nicht aktiv ist,
- ob der eigentliche Updater-Prompt gestartet wird.

Zusaetzlich gilt:

- `scene`, `state` und `image` starten ihren Prompt-Schritt direkt bei erfüllten Aktivierungsbedingungen.
- Updater-Ereignisse sollen ueber strukturierte Felder wie `event`, `updater`, `active`, `reason` und `prompt_start` beschrieben werden.
- Fuer `image` wird auch der Fall protokolliert, dass kein Run-Trigger vorliegt und deshalb kein Bildlauf startet.

### Bild-Logging

Fuer Bild-Updates wird zusaetzlich geloggt:

- ob eine Bildgenerierung gestartet wird,
- welcher Bild-Generierungsprompt verwendet wird,
- welches Bild als Quelle verwendet wird,
- wohin das neue Bild geschrieben wird,
- ob vor dem Schreiben ein Backup erzeugt wurde,
- falls ein Revert ausgefuehrt wird: ob der Revert erfolgreich war,
- falls ein Revert ausgefuehrt wird: aus welcher Quelle ein Bild wiederhergestellt wurde.
- Auch diese Informationen werden als strukturierte Events mit expliziten Feldern wie `source_image`, `target_image`, `prompt`, `backup` oder `restored_from` geschrieben.

## Akzeptanzkriterien

- Die Anwendung schreibt INFO-Logs nach `.data/app.log`.
- Chat-Aufrufe hinterlassen Token-Logs.
- Jeder Updater hinterlaesst Logs zu Aktivstatus und Prompt-Start.
- Der `image`-Workflow hinterlaesst Logs zu Generierung, Prompt, Quelle, Ziel und Backup; Revert-Logs nur bei tatsaechlich ausgefuehrtem Revert.




