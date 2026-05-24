---
state: implemented
---

# SG-023: Referenzbild fuer Locations

## Kontext
Das System unterstuetzt in der Web-GUI bereits das textbasierte Anlegen von Szenen fuer die aktive Figur.  
Diese Anforderung erweitert diesen Ablauf um ein optionales Referenzbild, aus dem eine Szenenbeschreibung oder ein Vorschaubild fuer die neue Location erzeugt werden kann.

## Annahmen
- Im Projekt bezeichnen `Location` und `Scene` denselben fachlichen Kontext.
- Der bestehende textbasierte Ablauf fuer das Anlegen einer Szene bleibt ohne Referenzbild fachlich unveraendert nutzbar.
- Der NPC-Kontext ist fachlich kein Bestandteil des Referenzbilds, sondern eine automatisch erstellte NPC-szenenspezifische Ergaenzung zur neu erstellten Location.
- Die Referenzbild-Auswahl erfolgt platzsparend ueber die Bildvorschau statt ueber einen separaten Button; dieses Verhalten entspricht aktuellen UI-Konventionen fuer Bildauswahlfelder.
- Die Aktion `Bild aus Beschreibung` ist auch ohne Referenzbild eine manuelle Vorschau-Aktion im Szene-Dialog.

## Offene Fragen
- Keine

## Fachlicher Ablauf

1. Der Nutzer oeffnet den bestehenden Dialog zum Anlegen einer Szene.
2. Der Nutzer kann wie bisher eine Szenenbeschreibung eingeben.
3. Optional waehlt der Nutzer ein Referenzbild aus.
4. Das System verkleinert das Referenzbild clientseitig auf eine fuer die weitere Verarbeitung geeignete Groesse.
5. Das verkleinerte Referenzbild erscheint als Vorschau, wird aber noch nicht dauerhaft gespeichert.
6. Der Nutzer kann die Szenenbeschreibung aus dem Referenzbild erzeugen lassen.
7. Der Nutzer kann aus der aktuellen Szenenbeschreibung manuell ein Vorschaubild erzeugen lassen; ist ein Referenzbild vorhanden, dient dieses als visuelle Basis.
8. Der Nutzer kann das Referenzbild wieder entfernen und damit zur textbasierten Erstellung ohne Referenzbild zurueckkehren.
9. Beim erfolgreichen Anlegen einer neuen Location wird ein vorhandenes erzeugtes Vorschaubild als Szenenbild uebernommen; ist nur ein Referenzbild vorhanden, erzeugt das System beim Anlegen daraus ein Szenenbild.
10. Das System erstellt aus derselben Beschreibung automatisch einen NPC-Kontext fuer die aktive Figur in der neuen Location.

## Anforderungen

### Referenzbild im Szene-Dialog
**Typ:** Funktional  
**Beschreibung:** Das System muss im bestehenden Dialog zum Anlegen einer Szene einen optionalen Referenzbild-Bereich bereitstellen.  
**Akzeptanzkriterien:**
- Der Dialog enthaelt weiterhin ein verpflichtendes Feld fuer die Szenenbeschreibung.
- Der Dialog bietet keine waehbare Erstelloption fuer den NPC-Kontext an.
- Beim Anlegen einer neuen Location wird automatisch ein NPC-Kontext fuer die aktive Figur erstellt.
- Eine NPC-Kontext-Erstellung ist nicht Teil der Referenzbild-Verarbeitung und verwendet das Referenzbild nicht als fachliche Eingabe.
- Im Bereich der Szenenbeschreibung ist ein Referenzbild-Bereich mit klickbarer Vorschau und Bildaktionen vorhanden.
- Die Szenenbeschreibung bleibt auch bei vorhandenem Referenzbild manuell bearbeitbar.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Auswahl und Verkleinerung des Referenzbilds
**Typ:** Funktional  
**Beschreibung:** Das System muss ein ausgewaehltes Referenzbild clientseitig auf eine fuer die weitere Verarbeitung geeignete Groesse verkleinern.  
**Akzeptanzkriterien:**
- Die Auswahl eines Referenzbilds ueber die Bildvorschau folgt `SG-025`.
- Nach der Bildauswahl wird das Bild clientseitig verkleinert, bevor es als Referenzbild fuer Beschreibungserzeugung oder Bildgenerierung verwendet wird.
- Die Verkleinerung bewahrt den sichtbaren Bildinhalt ohne manuelle Bildausschnitt-Auswahl.
- Nach erfolgreicher Verkleinerung zeigt die Vorschau das verkleinerte Referenzbild.
- Vor dem Speichern wird das Referenzbild nicht dauerhaft als Szenenbild gespeichert.

**Referenzen:** `doc/requirements/sg-025-einheitliches-vorschauverhalten-generierter-bilder.md`

### Vorschau des aktuellen Bildzustands
**Typ:** Funktional  
**Beschreibung:** Das System muss in der Vorschau den aktuellen Bildzustand fuer die neue Location anzeigen.  
**Akzeptanzkriterien:**
- Ohne Referenzbild und ohne erzeugtes Vorschaubild zeigt die Vorschau einen Platzhalter.
- Nach erfolgreicher Verkleinerung zeigt die Vorschau das verkleinerte Referenzbild als visuelle Basis.
- Nach erfolgreicher Bildgenerierung zeigt die Vorschau das zuletzt erzeugte Vorschaubild.
- Eine erfolgreiche Bildgenerierung ersetzt nur die Vorschau, nicht das gespeicherte Szenenbild.

**Referenzen:** Keine

### Overlay-Vorschau für erzeugte Vorschaubilder
**Typ:** Funktional  
**Beschreibung:** Das System muss für ein bereits erzeugtes Vorschaubild im Szene-Dialog das einheitliche Vorschauverhalten gemäß `SG-025` verwenden.  
**Akzeptanzkriterien:**
- Für ein erzeugtes Vorschaubild ist eine Overlay-Ansicht verfügbar.
- In der Overlay-Ansicht ist das zuletzt erzeugte Vorschaubild vollständig sichtbar.
- Das Klickverhalten der Bildvorschau richtet sich nach `SG-025`.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`, `doc/requirements/sg-025-einheitliches-vorschauverhalten-generierter-bilder.md`

### Beschreibung aus Referenzbild
**Typ:** Funktional  
**Beschreibung:** Das System muss aus dem aktuell gewaehlten Referenzbild eine Szenenbeschreibung erzeugen koennen.  
**Akzeptanzkriterien:**
- Die Aktion heisst `Beschreibung aus Bild`.
- Die Aktion ist nur ausfuehrbar, wenn ein Referenzbild vorhanden ist.
- Nach erfolgreicher Ausfuehrung ersetzt die erzeugte Beschreibung den bisherigen Inhalt des Beschreibungsfelds.
- Scheitert die Erzeugung, bleibt der bisherige Beschreibungstext unveraendert.

**Referenzen:** Keine

### Inhalt der erzeugten Szenenbeschreibung
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss die aus einem Referenzbild erzeugte Szenenbeschreibung auf die sichtbare Location ausrichten.  
**Akzeptanzkriterien:**
- Die erzeugte Beschreibung beschreibt sichtbare Umgebung, Atmosphaere, Licht, Einrichtung und relevante Details.
- Die erzeugte Beschreibung erfindet keine Figurenhandlungen, Ereignisse oder nicht sichtbaren Hintergrundgeschichten.

**Referenzen:** Keine

### Manuelles Vorschaubild aus Beschreibung
**Typ:** Funktional  
**Beschreibung:** Das System muss aus der aktuellen Szenenbeschreibung manuell ein temporaeres Vorschaubild erzeugen koennen.  
**Akzeptanzkriterien:**
- Die Aktion heisst `Bild aus Beschreibung`.
- Ist ein Referenzbild vorhanden, verwendet die Aktion die aktuelle Szenenbeschreibung und das verkleinerte Referenzbild.
- Ist kein Referenzbild vorhanden, verwendet die Aktion nur die aktuelle Szenenbeschreibung.
- Nach erfolgreicher Ausfuehrung zeigt die Vorschau das erzeugte Bild.
- Das erzeugte Vorschaubild wird erst beim erfolgreichen Anlegen einer neuen Location dauerhaft als Szenenbild uebernommen.
- Scheitert die Erzeugung, bleibt die bisherige Vorschau unveraendert.

**Referenzen:** `doc/requirements/sg-007-dreistufige-bildgenerierung.md`

### Stabile Referenzbasis
**Typ:** Funktional  
**Beschreibung:** Das System muss bei wiederholter referenzgestuetzter Bildgenerierung das urspruenglich verkleinerte Referenzbild als visuelle Basis beibehalten.  
**Akzeptanzkriterien:**
- `Bild aus Beschreibung` kann mit vorhandenem Referenzbild mehrfach nacheinander ausgefuehrt werden.
- Eine erneute Ausfuehrung verwendet nicht das zuletzt erzeugte Vorschaubild als neue Bildbasis.
- Das verkleinerte Referenzbild bleibt bis zum Entfernen der Referenz die visuelle Basis.

**Referenzen:** Keine

### Referenzbild entfernen
**Typ:** Funktional  
**Beschreibung:** Das System muss das aktuell gewaehlte Referenzbild aus dem Bearbeitungszustand des Dialogs entfernen koennen.  
**Akzeptanzkriterien:**
- Die Aktion ist als Entfernen- oder Loeschen-Aktion fuer das aktuell gewaehlte Bild erkennbar.
- Nach erfolgreicher Ausfuehrung ist kein Referenzbild mehr vorhanden.
- Nach erfolgreicher Ausfuehrung zeigt die Vorschau wieder den Platzhalter.
- Danach verhaelt sich `Bild aus Beschreibung` wie eine textbasierte Bildgenerierung ohne Referenzbild.

**Referenzen:** Keine

### Szenenbild beim Anlegen einer Location
**Typ:** Funktional  
**Beschreibung:** Das System muss beim Anlegen einer neuen Location ein vorhandenes erzeugtes Vorschaubild uebernehmen oder bei nur vorhandenem Referenzbild ein Szenenbild erzeugen.  
**Akzeptanzkriterien:**
- Wurde ein Vorschaubild erzeugt, wird das zuletzt sichtbare Vorschaubild als Szenenbild uebernommen.
- Wurde ein Referenzbild gewaehlt, aber kein Vorschaubild erzeugt, erzeugt das System beim Anlegen ein Szenenbild aus der aktuellen Szenenbeschreibung und dem verkleinerten Referenzbild.
- Die automatische Bildgenerierung beim Anlegen verwendet fachlich dieselbe Bildgenerierung wie die manuelle Aktion `Bild aus Beschreibung`.
- Schlaegt die automatische Bildgenerierung beim Anlegen fehl, schlaegt das Anlegen der Location fehl und das Referenzbild wird nicht ersatzweise als Szenenbild uebernommen.
- Das Referenzbild selbst wird nicht als Szenenbild uebernommen, solange daraus nicht erfolgreich ein Vorschaubild oder ein Szenenbild erzeugt wurde.
- Das gespeicherte Szenenbild ist danach als Bild der neu angelegten Location verfuegbar.
- Wenn ein erzeugtes Vorschaubild uebernommen wird, erzeugt das Anlegen der Location kein weiteres Szenenbild, das die Vorschau ersetzt.
- Ohne Referenzbild und ohne erzeugtes Vorschaubild entsteht durch das Referenzbild-Feature kein zusaetzliches Szenenbild.

**Referenzen:** `doc/requirements/sg-007-dreistufige-bildgenerierung.md`, `doc/requirements/sg-016-overrides-verzeichnis.md`

### Validierung von Referenzbildern
**Typ:** Randbedingung  
**Beschreibung:** Das System muss nur gueltige Referenzbilder innerhalb der festgelegten Grenzen verarbeiten.  
**Akzeptanzkriterien:**
- Nicht dekodierbare Dateien werden abgelehnt.
- Dateien ausserhalb von PNG, JPEG oder WebP werden abgelehnt.
- Das verarbeitete Referenzbild liegt nach der clientseitigen Verkleinerung bei hoechstens 5 MB.
- Das verarbeitete Referenzbild hat nach der clientseitigen Verkleinerung keine Kante ueber 1536 px.
- Abgelehnte Dateien veraendern weder Szenenbeschreibung noch Vorschau.

**Referenzen:** Keine

### Darstellung erzeugter Szenenbilder
**Typ:** Randbedingung  
**Beschreibung:** Das System muss erzeugte Szenenbilder als personenfreie Location-Bilder im bestehenden Bildformat bereitstellen.  
**Akzeptanzkriterien:**
- Ein erzeugtes Szenenbild zeigt die Location ohne Personen.
- Ein erzeugtes Szenenbild verwendet das fuer Szenenbilder bestehende Hochkantformat.
- Ein erzeugtes Szenenbild verwendet die fuer Szenenbilder bestehende Aufloesung.

**Referenzen:** `prompts/scene_create_image.md`
