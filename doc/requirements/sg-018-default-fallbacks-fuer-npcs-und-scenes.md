---
state: implemented
---

# SG-018: Neue NPCs und Scenes mit Default-Fallbacks

## Kontext
Das Projekt verwaltet versionierte Standard-Datensätze unter `npcs/` und `scenes/` sowie lokale Ergänzungen unter `.overrides/`.
SG-018 ergänzt `doc/requirements/sg-016-overrides-verzeichnis.md` um konfigurierbare Default-Fallbacks und das Anlegen neuer NPCs und Scenes im Override-Verzeichnis.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Weitere NPCs anlegen
**Typ:** Funktional  
**Beschreibung:** Das System muss weitere NPCs im Override-Verzeichnis anlegbar machen.  
**Akzeptanzkriterien:**
- Ein neuer NPC kann über ein CLI-Kommando angelegt werden.
- Das CLI-Kommando legt einen neuen NPC unter `.overrides/npcs/<npc_id>/` an.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Initiale Dateien für neue NPCs
**Typ:** Funktional  
**Beschreibung:** Das System muss beim Anlegen eines NPC unter `.overrides/npcs/<npc_id>/` nur die initial erforderlichen Override-Inhalte erzeugen.  
**Akzeptanzkriterien:**
- Nach dem Anlegen existiert `.overrides/npcs/<npc_id>/`.
- `.overrides/npcs/<npc_id>/character.yaml` wird erzeugt.
- Weitere NPC-Dateien werden beim Anlegen nicht erzeugt.
**Referenzen:** `npcs/`, `doc/requirements/sg-016-overrides-verzeichnis.md`

### Weitere Scenes anlegen
**Typ:** Funktional  
**Beschreibung:** Das System muss weitere Scenes im Override-Verzeichnis anlegbar machen.  
**Akzeptanzkriterien:**
- Eine neue Scene kann über ein CLI-Kommando angelegt werden.
- Das CLI-Kommando legt eine neue Scene unter `.overrides/scenes/<scene_id>/` an.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Initiale Dateien für neue Scenes
**Typ:** Funktional  
**Beschreibung:** Das System muss beim Anlegen einer Scene unter `.overrides/scenes/<scene_id>/` keine zusätzlichen Scene-Dateien erzeugen.  
**Akzeptanzkriterien:**
- Nach dem Anlegen existiert `.overrides/scenes/<scene_id>/`.
- `scene.md` wird beim Anlegen nicht erzeugt.
- `img.png` wird beim Anlegen nicht erzeugt.
**Referenzen:** `scenes/`, `doc/requirements/sg-016-overrides-verzeichnis.md`

### Konfigurierbare Default-NPC-ID
**Typ:** Randbedingung  
**Beschreibung:** Das System muss in `engine/config.py` eine `DEFAULT_NPC_ID` als Konfigurationswert vorsehen, die über eine Umgebungsvariable gesetzt werden kann.  
**Akzeptanzkriterien:**
- `DEFAULT_NPC_ID` ist in `engine/config.py` als Konfigurationswert vorhanden.
- Der Wert von `DEFAULT_NPC_ID` kann über eine Umgebungsvariable gesetzt werden.
**Referenzen:** `engine/config.py`

### Konfigurierbare Default-Scene-ID
**Typ:** Randbedingung  
**Beschreibung:** Das System muss in `engine/config.py` eine `DEFAULT_SCENE_ID` als Konfigurationswert vorsehen, die über eine Umgebungsvariable gesetzt werden kann.  
**Akzeptanzkriterien:**
- `DEFAULT_SCENE_ID` ist in `engine/config.py` als Konfigurationswert vorhanden.
- Der Wert von `DEFAULT_SCENE_ID` kann über eine Umgebungsvariable gesetzt werden.
**Referenzen:** `engine/config.py`

### Default-Fallback für fehlende NPC-Dateien
**Typ:** Funktional  
**Beschreibung:** Das System muss fehlende NPC-Dateien beim Laden über die bestehende Prioritätskette bis zum Default-NPC-Fallback bereitstellen.  
**Akzeptanzkriterien:**
- Fehlt beim Laden eines NPC eine Datei unter `.overrides/npcs/<npc_id>/`, wird die Datei nicht beim Anlegen erzeugt.
- Fehlt beim Laden eines NPC eine Datei in den vorherigen Ebenen der Prioritätskette, wird zuerst der statische Default des Ziel-NPC verwendet.
- Fehlt die Datei auch dort, wird die entsprechende Datei des durch `DEFAULT_NPC_ID` bezeichneten NPC verwendet.
**Referenzen:** `engine/config.py`, `engine/storage.py`

### Default-Fallback für fehlende Scene-Dateien
**Typ:** Funktional  
**Beschreibung:** Das System muss fehlende Scene-Dateien beim Laden über die bestehende Prioritätskette bis zum Default-Scene-Fallback bereitstellen.  
**Akzeptanzkriterien:**
- Fehlt beim Laden einer Scene eine Datei unter `.overrides/scenes/<scene_id>/`, wird die Datei nicht beim Anlegen erzeugt.
- Fehlt beim Laden einer Scene eine Datei in den vorherigen Ebenen der Prioritätskette, wird zuerst der statische Default der Ziel-Scene verwendet.
- Fehlt die Datei auch dort, wird die entsprechende Datei der durch `DEFAULT_SCENE_ID` bezeichneten Default-Scene verwendet.
**Referenzen:** `engine/config.py`, `scenes/`, `doc/requirements/sg-016-overrides-verzeichnis.md`

### Priorität des Default-NPC-Fallbacks
**Typ:** Randbedingung  
**Beschreibung:** Das System muss den Default-NPC als zusätzliche letzte Ebene in die bestehende Prioritätskette für NPC-Dateien einordnen.  
**Akzeptanzkriterien:**
- Für NPC-Dateien gilt die Reihenfolge Laufzeitdatei vor `.overrides/npcs/<npc_id>/` vor szenenspezifischem NPC-Asset vor statischem Default des Ziel-NPC vor Default-NPC.
- Der Default-NPC wird nur verwendet, wenn in allen vorherigen Ebenen kein Wert vorhanden ist.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Priorität des Default-Scene-Fallbacks
**Typ:** Randbedingung  
**Beschreibung:** Das System muss die Default-Scene als zusätzliche letzte Ebene in die bestehende Prioritätskette für Scene-Dateien einordnen.  
**Akzeptanzkriterien:**
- Für Scene-Dateien gilt die Reihenfolge Laufzeitdatei vor `.overrides/scenes/<scene_id>/` vor statischem Default der Ziel-Scene vor Default-Scene.
- Die Default-Scene wird nur verwendet, wenn in allen vorherigen Ebenen kein Wert vorhanden ist.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`
