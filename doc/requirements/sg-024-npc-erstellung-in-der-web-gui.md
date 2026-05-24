---
state: implemented
---

# SG-024: NPC-Erstellung in der Web-GUI

## Kontext
Das System unterstützt in der Web-GUI das Anlegen neuer NPCs als lokale Ergänzungen.
SG-024 bündelt die fachlichen Anforderungen zur NPC-Erstellung in der Web-GUI.
Der aktuelle Scope umfasst den bestehenden textbasierten Ablauf und ein optionales Referenzbild für die NPC-Profilerstellung.

## Annahmen
- Das Referenzbild ist eine optionale Unterstützung der NPC-Profilerstellung und gehört fachlich nicht zu einem NPC-Szenen-Kontext.
- Die fachliche Nutzerführung orientiert sich an `doc/requirements/sg-023-referenzbild-fuer-locations.md`.

## Offene Fragen
- Keine

## Anforderungen

### Anlegen von NPCs in der Web-GUI
**Typ:** Funktional  
**Beschreibung:** Das System muss das Anlegen neuer NPCs in der Web-GUI ermöglichen.  
**Akzeptanzkriterien:**
- Eine neue NPC-Erstellung kann in der Web-GUI aus demselben fachlichen Kontext wie die Szenen-Erstellung gestartet werden.
- Nach erfolgreichem Anlegen kehrt die Oberfläche zur Kontextauswahl zurück.
- Der neue NPC ist dort sichtbar und für die Nutzung in der Sitzung auswählbar.
- Fehlschläge des Anlegens werden nachvollziehbar angezeigt.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Initiale lokale Inhalte für neue NPCs
**Typ:** Funktional  
**Beschreibung:** Das System muss neue NPCs als lokale Ergänzungen mit den initial erforderlichen Inhalten anlegen.  
**Akzeptanzkriterien:**
- Nach erfolgreichem Anlegen existiert ein eigener lokaler Bereich für den NPC.
- Der neue NPC wird nicht als versionierter Standardinhalt angelegt.
- Nach dem Anlegen sind eine Charakterbeschreibung, ein initialer Zustand und ein Charakterbild für den NPC vorhanden.
- Die erzeugten Inhalte orientieren sich fachlich am Aufbau vorhandener NPC-Inhalte.

**Referenzen:** `npcs/`, `doc/requirements/sg-005-npc-bilder.md`, `doc/requirements/sg-016-overrides-verzeichnis.md`

### Beschreibung als verpflichtende Eingabe für neue NPCs
**Typ:** Funktional  
**Beschreibung:** Das System muss das Anlegen neuer NPCs auf eine vom Nutzer angegebene Beschreibung als verpflichtende fachliche Eingabe stützen.  
**Akzeptanzkriterien:**
- Die Web-GUI nimmt für das Anlegen eines NPC eine Beschreibung entgegen.
- Für das Anlegen eines neuen NPC sind keine weiteren verpflichtenden fachlichen Eingaben erforderlich.
- Die NPC-Erstellung ist nur ausführbar, wenn eine Beschreibung vorhanden ist.
- In der Beschreibung ausdrücklich genannte Fakten werden im neuen NPC berücksichtigt.
- Fehlende Charaktereigenschaften werden passend ergänzt.

**Referenzen:** Keine

### Optionales Referenzbild in der NPC-Erstellung
**Typ:** Funktional  
**Beschreibung:** Das System muss im bestehenden Dialog zum Anlegen eines NPC ein optionales Referenzbild anbieten.  
**Akzeptanzkriterien:**
- Im Dialog ist zusätzlich ein Bereich zum Auswählen eines optionalen Referenzbilds vorhanden.
- Die NPC-Erstellung bleibt ohne Referenzbild nutzbar.
- Die NPC-Beschreibung bleibt auch bei vorhandenem Referenzbild manuell bearbeitbar.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`, `doc/requirements/sg-023-referenzbild-fuer-locations.md`

### Auswahl und Verkleinerung des Referenzbilds
**Typ:** Funktional  
**Beschreibung:** Das System muss ein ausgewaehltes Referenzbild clientseitig auf eine fuer die weitere Verarbeitung geeignete Groesse verkleinern.  
**Akzeptanzkriterien:**
- Die Auswahl eines Referenzbilds über die Bildvorschau folgt `SG-025`.
- Nach der Bildauswahl wird das Bild clientseitig verkleinert, bevor es als Referenzbild fuer Beschreibungserzeugung oder Bildgenerierung verwendet wird.
- Die Verkleinerung bewahrt den sichtbaren Bildinhalt ohne manuelle Bildausschnitt-Auswahl.
- Nach erfolgreicher Verkleinerung zeigt die Vorschau das verkleinerte Referenzbild.
- Vor dem Speichern wird das Referenzbild nicht dauerhaft als NPC-Profilbild gespeichert.

**Referenzen:** `doc/requirements/sg-023-referenzbild-fuer-locations.md`, `doc/requirements/sg-025-einheitliches-vorschauverhalten-generierter-bilder.md`

### Vorschau des aktuellen Profilbildzustands
**Typ:** Funktional  
**Beschreibung:** Das System muss im Dialog den aktuellen Profilbildzustand fuer den neuen NPC anzeigen.  
**Akzeptanzkriterien:**
- Ohne ausgewähltes Referenzbild und ohne erzeugtes Vorschaubild zeigt die Vorschau einen Platzhalter.
- Nach erfolgreicher Verkleinerung zeigt die Vorschau das verkleinerte Referenzbild als visuelle Basis.
- Nach erfolgreicher Bilderzeugung zeigt die Vorschau das zuletzt erzeugte Vorschaubild.
- Vor dem erfolgreichen Anlegen des NPC wird das angezeigte Bild noch nicht als NPC-Profilbild des neuen NPC gespeichert.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`

### Overlay-Vorschau für erzeugte Vorschaubilder
**Typ:** Funktional  
**Beschreibung:** Das System muss für ein bereits erzeugtes Vorschaubild im NPC-Dialog das einheitliche Vorschauverhalten gemäß `SG-025` verwenden.  
**Akzeptanzkriterien:**
- Für ein erzeugtes Vorschaubild ist eine Overlay-Ansicht verfügbar.
- In der Overlay-Ansicht ist das zuletzt erzeugte Vorschaubild vollständig sichtbar.
- Das Klickverhalten der Bildvorschau richtet sich nach `SG-025`.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`, `doc/requirements/sg-025-einheitliches-vorschauverhalten-generierter-bilder.md`

### Beschreibung aus Referenzbild
**Typ:** Funktional  
**Beschreibung:** Das System muss aus einem ausgewählten Referenzbild eine NPC-Beschreibung erzeugen können.  
**Akzeptanzkriterien:**
- Die Aktion heißt `Beschreibung aus Bild`.
- Die Aktion ist nur ausführbar, wenn ein Referenzbild vorhanden ist.
- Nach erfolgreicher Ausführung ersetzt die erzeugte Beschreibung den bisherigen Inhalt des Beschreibungsfelds.
- Scheitert die Erzeugung, bleibt der bisherige Beschreibungstext unverändert.

**Referenzen:** Keine

### Inhalt der erzeugten NPC-Beschreibung
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss eine aus einem Referenzbild erzeugte NPC-Beschreibung auf sichtbare Merkmale der dargestellten Figur begrenzen.  
**Akzeptanzkriterien:**
- Die erzeugte Beschreibung beschreibt sichtbare Erscheinung, Kleidung, Haltung, Ausstrahlung und andere wiedererkennbare visuelle Merkmale.
- Die erzeugte Beschreibung behauptet keine Identität der abgebildeten Person als gesicherte Tatsache.
- Die erzeugte Beschreibung leitet keine sensiblen Eigenschaften aus dem Bild ab.
- Die erzeugte Beschreibung erfindet keine nicht sichtbare Biografie, keine Beziehungen und keine Ereignisse.

**Referenzen:** Keine

### Manuelles Profilbild aus Beschreibung
**Typ:** Funktional  
**Beschreibung:** Das System muss aus der aktuellen NPC-Beschreibung ein temporäres Profilbild für den neuen NPC erzeugen können.  
**Akzeptanzkriterien:**
- Die Aktion heißt `Bild aus Beschreibung`.
- Die Aktion ist auch ohne Referenzbild ausführbar.
- Ist ein Referenzbild vorhanden, kann das erzeugte Vorschaubild sich zusätzlich an diesem Referenzbild orientieren.
- Nach erfolgreicher Ausführung zeigt die Vorschau das erzeugte Bild.
- Scheitert die Erzeugung, bleibt die bisherige Vorschau unverändert.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`, `doc/requirements/sg-023-referenzbild-fuer-locations.md`

### Stabile Referenzbasis für wiederholte Bilderzeugung
**Typ:** Funktional  
**Beschreibung:** Das System muss bei wiederholter Bilderzeugung mit Referenzbild das ursprünglich verkleinerte Referenzbild als fachliche Bildbasis beibehalten.  
**Akzeptanzkriterien:**
- `Bild aus Beschreibung` kann mit vorhandenem Referenzbild mehrfach nacheinander ausgeführt werden.
- Eine erneute Ausführung verwendet nicht das zuletzt erzeugte Vorschaubild als neue Referenz.
- Das verkleinerte Referenzbild bleibt bis zum Entfernen des Referenzbilds die Bildbasis.

**Referenzen:** `doc/requirements/sg-023-referenzbild-fuer-locations.md`

### Referenzbild entfernen
**Typ:** Funktional  
**Beschreibung:** Das System muss ein ausgewähltes Referenzbild aus dem aktuellen Bearbeitungszustand der NPC-Erstellung entfernen können.  
**Akzeptanzkriterien:**
- Für ein vorhandenes Referenzbild ist eine erkennbare Entfernen- oder Löschen-Aktion vorhanden.
- Nach erfolgreicher Ausführung ist kein Referenzbild mehr ausgewählt.
- Danach verhält sich `Bild aus Beschreibung` wieder wie eine Bilderzeugung ohne Referenzbild.

**Referenzen:** `doc/requirements/sg-023-referenzbild-fuer-locations.md`

### Profilbild beim Anlegen eines NPC
**Typ:** Funktional  
**Beschreibung:** Das System muss beim Anlegen eines neuen NPC ein vorhandenes erzeugtes Vorschaubild übernehmen oder bei nur vorhandenem Referenzbild ein Profilbild erzeugen.  
**Akzeptanzkriterien:**
- Wird ein erzeugtes Vorschaubild angezeigt, wird dieses beim erfolgreichen Anlegen als initiales NPC-Profilbild des neuen NPC übernommen.
- Wird ein Referenzbild angezeigt, aber kein Vorschaubild erzeugt, erzeugt das System beim Anlegen ein initiales NPC-Profilbild aus der aktuellen NPC-Beschreibung und dem verkleinerten Referenzbild.
- Die automatische Bilderzeugung beim Anlegen verwendet fachlich dieselbe Bilderzeugung wie die manuelle Aktion `Bild aus Beschreibung`.
- Schlägt die automatische Bilderzeugung beim Anlegen fehl, schlägt das Anlegen des NPC fehl und das Referenzbild wird nicht ersatzweise als initiales NPC-Profilbild übernommen.
- Das Referenzbild selbst wird nicht als initiales NPC-Profilbild übernommen, solange daraus nicht erfolgreich ein Vorschaubild oder Profilbild erzeugt wurde.
- Ist weder ein Referenzbild noch ein erzeugtes Vorschaubild sichtbar, gelten die bestehenden Regeln für initiale NPC-Inhalte.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`

### Verarbeitbare Referenzbilder
**Typ:** Randbedingung  
**Beschreibung:** Das System darf nur Referenzbilder verarbeiten, die für den vorgesehenen Ablauf nutzbar sind.  
**Akzeptanzkriterien:**
- Nicht lesbare Bilddateien werden abgelehnt.
- Nicht unterstützte Bilddateien werden abgelehnt.
- Das verarbeitete Referenzbild liegt nach der clientseitigen Verkleinerung bei hoechstens 5 MB.
- Das verarbeitete Referenzbild hat nach der clientseitigen Verkleinerung keine Kante ueber 1536 px.
- Abgelehnte Dateien verändern weder die NPC-Beschreibung noch die Vorschau.

**Referenzen:** Keine

### Charaktergerechte Darstellung erzeugter Profilbilder
**Typ:** Randbedingung  
**Beschreibung:** Das System muss erzeugte Profilbilder so ausrichten, dass der neue NPC als Hauptmotiv erkennbar bleibt.  
**Akzeptanzkriterien:**
- Ein erzeugtes Profilbild zeigt den neuen NPC als erkennbares Hauptmotiv.
- Andere Personen erscheinen nicht als zentrales Hauptmotiv des Profilbilds.
- Ein erzeugtes Profilbild folgt dem für NPC-Profilbilder bestehenden Bildformat.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`
