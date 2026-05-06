---
state: implemented
---

# SG-018: Neue NPCs und Scenes mit Default-Fallbacks

## Kontext
Das Projekt verwaltet Standardinhalte für NPCs und Scenes sowie lokale Ergänzungen.
SG-018 ergänzt `doc/requirements/sg-016-overrides-verzeichnis.md` um Regeln für neue NPCs und Scenes, NPC-szenenspezifische Ergänzungen und Default-Fallbacks.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Weitere NPCs anlegen
**Typ:** Funktional  
**Beschreibung:** Das System muss neue NPCs als lokale Ergänzungen anlegbar machen.  
**Akzeptanzkriterien:**
- Ein neuer NPC kann über den vorgesehenen Befehl angelegt werden.
- Für den neuen NPC wird ein eigener lokaler Bereich angelegt.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Initiale Dateien für neue NPCs
**Typ:** Funktional  
**Beschreibung:** Das System muss beim Anlegen eines NPC nur die initial erforderlichen Inhalte erzeugen.  
**Akzeptanzkriterien:**
- Nach dem Anlegen existiert ein eigener lokaler Bereich für den NPC.
- Dabei wird nur die initial erforderliche Charakterbeschreibung erzeugt.
- Weitere NPC-Inhalte werden dabei nicht automatisch erzeugt.
**Referenzen:** `npcs/`, `doc/requirements/sg-016-overrides-verzeichnis.md`

### Weitere Scenes anlegen
**Typ:** Funktional  
**Beschreibung:** Das System muss neue Scenes über `scene-create` als lokale Ergänzungen anlegbar machen.  
**Akzeptanzkriterien:**
- Eine neue Scene kann über `scene-create` angelegt werden.
- Für die neue Scene wird ein eigener lokaler Bereich angelegt.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Kurzbeschreibung als einzige Eingabe für neue Scenes
**Typ:** Funktional  
**Beschreibung:** Das System muss `scene-create` auf eine Kurzbeschreibung als einzige Eingabe beschränken.  
**Akzeptanzkriterien:**
- `scene-create` nimmt eine Kurzbeschreibung entgegen.
- Für das Anlegen einer neuen Scene sind keine weiteren Eingaben erforderlich.
**Referenzen:** Keine

### LLM-basierte Ableitung des finalen Scene-Namens
**Typ:** Funktional  
**Beschreibung:** Das System muss den finalen Scene-Namen aus der Kurzbeschreibung ableiten.  
**Akzeptanzkriterien:**
- Der finale Scene-Name wird aus der Kurzbeschreibung abgeleitet.
- Der finale Scene-Name wird nicht direkt als Eingabe übergeben.
**Referenzen:** `prompts/scene_create_text.md`

### LLM-Erzeugung der Szenenbeschreibung für neue Scenes
**Typ:** Funktional  
**Beschreibung:** Das System muss beim Anlegen einer neuen Scene eine Szenenbeschreibung erzeugen.  
**Akzeptanzkriterien:**
- Nach erfolgreichem Anlegen liegt für die neue Scene eine Szenenbeschreibung vor.
- Die Szenenbeschreibung wird aus der Kurzbeschreibung erzeugt.
**Referenzen:** `prompts/scene_create_text.md`

### Automatische Erzeugung der NPC-Scene-Ergänzung für neue Scenes
**Typ:** Funktional  
**Beschreibung:** Das System muss beim Anlegen einer neuen Scene zusätzlich eine NPC-szenenspezifische Ergänzung erzeugen.  
**Akzeptanzkriterien:**
- Nach erfolgreichem Anlegen der neuen Scene liegt eine NPC-szenenspezifische Ergänzung vor.
- Für die Ergänzung wird dieselbe Kurzbeschreibung wie für das Anlegen der Scene verwendet.
- Die Ergänzung bezieht sich auf den aktiven NPC und die neu angelegte aktive Scene.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Automatischer Anstoß der Szenenbildgenerierung für neue Scenes
**Typ:** Funktional  
**Beschreibung:** Das System muss beim erfolgreichen Anlegen einer neuen Scene die Bildgenerierung automatisch anstoßen, wenn die automatische Bildgenerierung aktiviert ist.  
**Akzeptanzkriterien:**
- Nach erfolgreichem Anlegen einer neuen Scene wird die Bildgenerierung ohne zusätzlichen manuellen Schritt angestoßen, wenn die automatische Bildgenerierung aktiviert ist.
- Ist die automatische Bildgenerierung nicht aktiviert, wird beim Anlegen der neuen Scene kein automatischer Anstoß der Bildgenerierung ausgelöst.
**Referenzen:** `prompts/scene_create_image.md`, `doc/requirements/sg-007-dreistufige-bildgenerierung.md`

### Personenfreie Darstellung im automatisch erzeugten Szenenbild
**Typ:** Randbedingung  
**Beschreibung:** Das System muss das automatisch erzeugte Szenenbild auf die Location ohne Personen beschränken.  
**Akzeptanzkriterien:**
- Das erzeugte Bild zeigt die Location.
- Das erzeugte Bild zeigt keine Personen.
**Referenzen:** `prompts/scene_create_image.md`

### Gleiches Hochkantformat für automatisch erzeugte Szenenbilder
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss automatisch erzeugte Szenenbilder im gleichen Hochkantformat und in der gleichen Auflösung wie die übrigen Bilder bereitstellen.  
**Akzeptanzkriterien:**
- Das erzeugte Bild verwendet dasselbe Hochkantformat wie die anderen Bilder.
- Das erzeugte Bild verwendet dieselbe Auflösung wie die anderen Bilder.
**Referenzen:** `prompts/scene_create_image.md`

### Fortlaufendes Suffix bei bestehendem Scene-Zielverzeichnis
**Typ:** Randbedingung  
**Beschreibung:** Das System muss bei einer bereits verwendeten abgeleiteten Scene-ID automatisch eine freie Scene-ID bilden.  
**Akzeptanzkriterien:**
- Existiert der vorgesehene lokale Bereich bereits, wird dieser nicht überschrieben.
- Stattdessen wird eine freie Scene-ID mit fortlaufendem numerischem Suffix verwendet.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Format und Ausschlüsse der generierten NPC-Scene-Beschreibung
**Typ:** Randbedingung  
**Beschreibung:** Das System muss die beim Anlegen einer neuen Scene zusätzlich erzeugte NPC-szenenspezifische Beschreibung grob gemäß den Prompt-Regeln zum Textformat und zu ausgeschlossenen Inhalten bereitstellen.  
**Akzeptanzkriterien:**
- Die erzeugte Beschreibung folgt dem vorgegebenen Textformat.
- Die erzeugte Beschreibung enthält keine laut Prompt ausgeschlossenen Inhaltsarten.
**Referenzen:** `prompts/npc_scene_create_text.md`

### Konfigurierbare Default-NPC-ID
**Typ:** Randbedingung  
**Beschreibung:** Das System muss eine konfigurierbare Default-NPC-ID vorsehen.  
**Akzeptanzkriterien:**
- Eine Default-NPC-ID ist als Konfigurationswert vorhanden.
- Der Konfigurationswert kann über die Umgebung gesetzt werden.
**Referenzen:** `engine/config.py`

### Konfigurierbare Default-Scene-ID
**Typ:** Randbedingung  
**Beschreibung:** Das System muss eine konfigurierbare Default-Scene-ID vorsehen.  
**Akzeptanzkriterien:**
- Eine Default-Scene-ID ist als Konfigurationswert vorhanden.
- Der Konfigurationswert kann über die Umgebung gesetzt werden.
**Referenzen:** `engine/config.py`

### Default-Fallback für fehlende NPC-Dateien
**Typ:** Funktional  
**Beschreibung:** Das System muss fehlende NPC-Inhalte beim Laden bis zum Default-NPC-Fallback auflösen.  
**Akzeptanzkriterien:**
- Fehlende lokale NPC-Inhalte werden nicht automatisch beim Anlegen erzeugt.
- Fehlt ein NPC-Inhalt in den vorherigen Ebenen der Prioritätskette, wird zuerst der Standardinhalt des Ziel-NPC verwendet.
- Fehlt der Inhalt auch dort, wird der entsprechende Inhalt des konfigurierten Default-NPC verwendet.
**Referenzen:** `engine/config.py`, `engine/storage.py`

### Default-Fallback für fehlende Scene-Dateien
**Typ:** Funktional  
**Beschreibung:** Das System muss fehlende Scene-Inhalte beim Laden bis zum Default-Scene-Fallback auflösen.  
**Akzeptanzkriterien:**
- Fehlende lokale Scene-Inhalte werden nicht automatisch beim Anlegen erzeugt.
- Fehlt ein Scene-Inhalt in den vorherigen Ebenen der Prioritätskette, wird zuerst der Standardinhalt der Ziel-Scene verwendet.
- Fehlt der Inhalt auch dort, wird der entsprechende Inhalt der konfigurierten Default-Scene verwendet.
**Referenzen:** `engine/config.py`, `scenes/`, `doc/requirements/sg-016-overrides-verzeichnis.md`

### Priorität des Default-NPC-Fallbacks
**Typ:** Randbedingung  
**Beschreibung:** Das System muss den Default-NPC als zusätzliche letzte Ebene in die bestehende Prioritätskette für NPC-Inhalte einordnen.  
**Akzeptanzkriterien:**
- Für NPC-Inhalte gilt die Reihenfolge Laufzeitdaten vor lokaler Ergänzung vor szenenspezifischem NPC-Inhalt vor Standardinhalt des Ziel-NPC vor Default-NPC.
- Der Default-NPC wird nur verwendet, wenn in allen vorherigen Ebenen kein Wert vorhanden ist.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Priorität des Default-Scene-Fallbacks
**Typ:** Randbedingung  
**Beschreibung:** Das System muss die Default-Scene als zusätzliche letzte Ebene in die bestehende Prioritätskette für Scene-Inhalte einordnen.  
**Akzeptanzkriterien:**
- Für Scene-Inhalte gilt die Reihenfolge Laufzeitdaten vor lokaler Ergänzung vor Standardinhalt der Ziel-Scene vor Default-Scene.
- Die Default-Scene wird nur verwendet, wenn in allen vorherigen Ebenen kein Wert vorhanden ist.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`
