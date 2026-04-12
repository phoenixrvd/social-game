---
state: defined
---

# ADR-009: Zentrale Pfadverwaltung in `storage.py`

## Status
defined

## Kontext
- Das Projekt verwendet drei Datenschichten mit fester Auflösungsreihenfolge: versionierte Quelldaten unter `npcs/` und `scenes/`, lokale Überschreibungen unter `.overrides/` und Laufzeitdaten unter `.data/`.
- In `engine/storage.py` sind die Prioritätsregeln `override > default` für Originaldateien sowie `runtime > override > default` für auflösbare Dateien implementiert; `NpcStorageView`, `SceneStorageView`, `PromptStorageView` und `Storage` kapseln die Dateizugriffe.

## Entscheidung
- Alle Dateizugriffe auf NPC-, Szenen- und Prompt-Daten laufen ausschließlich über `engine/storage.py`.
- Module verwenden für Dateizugriffe nicht direkt `config.NPC_DIR`, `config.SCENE_DIR`, `config.OVERRIDES_*` oder `config.DATA_*`, sondern die zentralen Zugriffe `storage.npc`, `storage.scene` und `storage.prompts`.
- Die Prioritätskette `runtime > override > default` beziehungsweise `override > default` ist einmalig in `engine/storage.py` definiert und gilt systemweit.

## Begründung
- Dezentrale Pfadbildung in einzelnen Modulen kennt die Override- und Runtime-Varianten nicht zuverlässig und lädt dadurch Dateien aus der falschen Datenschicht.
- Die Prioritätslogik würde sonst in mehreren Modulen dupliziert und bei Änderungen mehrfach angepasst werden müssen.
- Eine zentrale Auflösung verhindert, dass Module unbemerkt auf unterschiedliche Schichten schreiben oder lesen und sich Inhalte gegenseitig überschreiben.

## Alternativen
### Alternative 1
- Pfade pro Modul direkt aus `config.NPC_DIR`, `config.SCENE_DIR`, `config.OVERRIDES_*` und `config.DATA_*` zusammensetzen.
- Verworfen, weil dadurch Prioritätslogik dupliziert wird und das Überladen über Default-, Override- und Runtime-Schicht nicht mehr konsistent beherrschbar ist.

### Alternative 2
- Nur die Basispfade zentral in `engine/config.py` definieren und die eigentliche Auflösung der Kandidaten in den Fachmodulen belassen.
- Verworfen, weil `engine/config.py` zwar die Pfadkonfiguration liefert, aber keine einheitliche Auswahlregel wie `preferred_file(...)` und `first_existing_file(...)` erzwingt; die systemweite Priorisierung wäre damit weiter dezentral.

## Konsequenzen
- positiv: Die Auflösungsregeln für Default-, Override- und Runtime-Dateien sind an genau einer Stelle definiert.
- positiv: Änderungen an der Prioritätskette oder an Verzeichnisstrukturen müssen nur in `engine/storage.py` nachvollzogen werden.
- negativ: Module werden für Dateizugriffe bewusst an `engine/storage.py` gekoppelt.
- offen: Keine

## Annahmen
- Keine

## Offene Fragen
- Keine

## Referenzen
- `engine/storage.py`
- `engine/config.py`
- `doc/adr/002-datenspeicherung-data-verzeichnis.md`
- `doc/requirements/sg-016-overrides-verzeichnis.md`

