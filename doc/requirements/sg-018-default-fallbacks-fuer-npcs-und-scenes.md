---
state: defined
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

### Weitere NPCs in der Web-GUI anlegen
**Typ:** Funktional  
**Beschreibung:** Das System muss neue NPCs über die Web-GUI als lokale Ergänzungen anlegbar machen.  
**Akzeptanzkriterien:**
- Ein neuer NPC kann in der Web-GUI angelegt werden.
- Für den neuen NPC wird ein eigener lokaler Bereich angelegt.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Initiale Dateien für neue NPCs
**Typ:** Funktional  
**Beschreibung:** Das System muss beim Anlegen eines NPC die initial erforderlichen Inhalte erzeugen.  
**Akzeptanzkriterien:**
- Nach dem Anlegen existiert ein eigener lokaler Bereich für den NPC.
- Dabei werden eine Charakterbeschreibung, ein initialer Zustand und ein Charakterbild erzeugt.
- Die erzeugten Inhalte orientieren sich am Aufbau vorhandener NPC-Inhalte.
**Referenzen:** `npcs/`, `prompts/npc_create_description.md`, `prompts/npc_create_state.md`,
`prompts/npc_create_image.md`, `doc/requirements/sg-016-overrides-verzeichnis.md`

### Beschreibung als einzige Eingabe für neue NPCs

**Typ:** Funktional  
**Beschreibung:** Das System muss das Anlegen neuer NPCs auf eine vom Nutzer angegebene Beschreibung als einzige fachliche Eingabe beschränken.  
**Akzeptanzkriterien:**

- Die Web-GUI nimmt für das Anlegen eines NPC eine Beschreibung entgegen.
- Für das Anlegen eines neuen NPC sind keine weiteren fachlichen Eingaben erforderlich.
- In der Beschreibung ausdrücklich genannte Fakten werden im neuen NPC berücksichtigt.
- Fehlende Charaktereigenschaften werden passend ergänzt.
**Referenzen:** `prompts/npc_create_description.md`, `prompts/npc_create_state.md`

### Weitere Scenes anlegen
**Typ:** Funktional  
**Beschreibung:** Das System muss neue Scenes über die Web-GUI als lokale Ergänzungen anlegbar machen.  
**Akzeptanzkriterien:**
- Eine neue Scene kann in der Web-GUI angelegt werden.
- Für die neue Scene wird ein eigener lokaler Bereich angelegt.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Kurzbeschreibung als einzige Eingabe für neue Scenes
**Typ:** Funktional  
**Beschreibung:** Das System muss das Anlegen neuer Scenes auf eine Kurzbeschreibung als einzige fachliche Eingabe beschränken.  
**Akzeptanzkriterien:**
- Die Web-GUI nimmt für das Anlegen einer Scene eine Kurzbeschreibung entgegen.
- Für das Anlegen einer neuen Scene sind keine weiteren fachlichen Texteingaben erforderlich.
- Nutzer können entscheiden, ob aus derselben Kurzbeschreibung eine Scene, ein NPC-Kontext oder beides erstellt wird.
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

### Erzeugung der NPC-Scene-Ergänzung aus der Scene-Beschreibung
**Typ:** Funktional  
**Beschreibung:** Das System muss aus der eingegebenen Kurzbeschreibung optional eine NPC-szenenspezifische Ergänzung erzeugen.  
**Akzeptanzkriterien:**
- Ist `NPC Kontext erstellen` aktiv, wird eine NPC-szenenspezifische Ergänzung erzeugt.
- Für die Ergänzung wird dieselbe Kurzbeschreibung wie für das Anlegen der Scene verwendet.
- Ist gleichzeitig `Scene Erstellen` aktiv, bezieht sich die Ergänzung auf den aktiven NPC und die neu angelegte aktive Scene.
- Ist `Scene Erstellen` nicht aktiv, bezieht sich die Ergänzung auf den aktiven NPC und die bereits aktive Scene.
- Ist `NPC Kontext erstellen` nicht aktiv, wird keine NPC-szenenspezifische Ergänzung erzeugt.
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

### Optionale Löschung erstellter NPCs beim Verlauf-Löschen
**Typ:** Funktional  
**Beschreibung:** Das System muss erstellte NPCs optional zusammen mit dem Verlauf löschen können.  
**Akzeptanzkriterien:**
- Wird `Verlauf löschen` mit aktivierter Checkbox `Erstellten NPC mit löschen` bestätigt, ist der aktive erstellte NPC danach nicht mehr auswählbar.
- Die zum gelöschten NPC gehörenden erzeugten Inhalte sind danach nicht mehr vorhanden.
- Nach erfolgreicher Ausführung ist die aktive Sitzung auf den Default-NPC zurückgesetzt.
**Referenzen:** `doc/requirements/sg-009-git-basierte-spielstandshistorie.md`, `doc/requirements/sg-011-web-gui.md`

### Optionale Löschung erstellter Szenen beim Verlauf-Löschen
**Typ:** Funktional  
**Beschreibung:** Das System muss erstellte Szenen optional zusammen mit dem Verlauf löschen können.  
**Akzeptanzkriterien:**
- Wird `Verlauf löschen` mit aktivierter Checkbox `Erstellte Szene mit löschen` bestätigt, ist die aktive erstellte Szene danach nicht mehr auswählbar.
- Die zur gelöschten Szene gehörenden erzeugten Inhalte sind danach nicht mehr vorhanden.
- Nach erfolgreicher Ausführung ist die aktive Sitzung auf die Default-Szene zurückgesetzt.
**Referenzen:** `doc/requirements/sg-009-git-basierte-spielstandshistorie.md`, `doc/requirements/sg-011-web-gui.md`

### Optionale Löschung des NPC-Kontexts beim Verlauf-Löschen
**Typ:** Funktional  
**Beschreibung:** Das System muss den NPC-szenenspezifischen Kontext der aktiven Sitzung optional zusammen mit dem Verlauf löschen können.  
**Akzeptanzkriterien:**
- Wird `Verlauf löschen` mit aktivierter Checkbox `Erstellten NPC-Kontext löschen` bestätigt, ist der NPC-szenenspezifische Kontext für den aktiven NPC in der aktiven Szene danach nicht mehr vorhanden.
- Wird nur `Erstellten NPC-Kontext löschen` aktiviert, bleiben aktiver NPC und aktive Scene erhalten.
- Wird `Erstellten NPC mit löschen` aktiviert, wird die Löschung des NPC-szenenspezifischen Kontexts automatisch mit ausgewählt.
- Wird `Erstellte Szene mit löschen` aktiviert, wird die Löschung des NPC-szenenspezifischen Kontexts automatisch mit ausgewählt.
- Ist `Erstellten NPC mit löschen` nicht aktivierbar, kann die Löschung des NPC-szenenspezifischen Kontexts separat ausgewählt werden.
**Referenzen:** `doc/requirements/sg-011-web-gui.md`, `doc/requirements/sg-016-overrides-verzeichnis.md`

### Gleichzeitige Rücksetzung beider Löschoptionen
**Typ:** Funktional  
**Beschreibung:** Das System muss bei gleichzeitig aktivierten Löschoptionen beide Rücksetzungen ausführen.  
**Akzeptanzkriterien:**
- Wird `Verlauf löschen` mit aktivierten Checkboxen `Erstellten NPC mit löschen` und `Erstellte Szene mit löschen` bestätigt, zeigt die aktive Sitzung danach den Default-NPC in der Default-Szene.
**Referenzen:** `doc/requirements/sg-009-git-basierte-spielstandshistorie.md`, `doc/requirements/sg-011-web-gui.md`

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

### Angepasster Default-Fallback für fehlende NPC-Scene-Ergänzungen
**Typ:** Funktional  
**Beschreibung:** Das System muss fehlende NPC-szenenspezifische Ergänzungen über den Default-NPC so bereitstellen, dass sie zum aktiven NPC passen.  
**Akzeptanzkriterien:**
- Fehlt für den aktiven NPC in der aktiven Scene eine eigene NPC-szenenspezifische Ergänzung, wird die entsprechende Ergänzung des Default-NPC als fachliche Grundlage verwendet.
- Die bereitgestellte Ergänzung ist auf den aktiven NPC bezogen und übernimmt keine Identität oder Fakten des Default-NPC, die dem aktiven NPC widersprechen.
- Eine vorhandene NPC-szenenspezifische Ergänzung des aktiven NPC wird nicht durch den Default-Fallback ersetzt.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`, `prompts/npc_scene_create_text.md`

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
- Bei NPC-szenenspezifischen Ergänzungen wird ein verwendeter Default-NPC-Fallback fachlich an den aktiven NPC angepasst.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Priorität des Default-Scene-Fallbacks
**Typ:** Randbedingung  
**Beschreibung:** Das System muss die Default-Scene als zusätzliche letzte Ebene in die bestehende Prioritätskette für Scene-Inhalte einordnen.  
**Akzeptanzkriterien:**
- Für Scene-Inhalte gilt die Reihenfolge Laufzeitdaten vor lokaler Ergänzung vor Standardinhalt der Ziel-Scene vor Default-Scene.
- Die Default-Scene wird nur verwendet, wenn in allen vorherigen Ebenen kein Wert vorhanden ist.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`
