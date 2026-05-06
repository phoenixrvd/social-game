---
state: implemented
---

# SG-011: Web-GUI

## Kontext
Das System stellt eine Web-GUI als Benutzeroberfläche bereit.  
Der fachliche Fokus liegt auf der Nutzung der Spielinteraktion über den Browser.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Interaktion über Weboberfläche
**Typ:** Funktional  
**Beschreibung:** Das System muss die fachlichen Kerninteraktionen einer aktiven Sitzung über die Web-GUI ermöglichen.  
**Akzeptanzkriterien:**
- Nutzereingaben können über die Web-GUI erfasst und abgesendet werden.
- Abgesendete Nutzereingaben erscheinen im Dialogverlauf der aktiven Sitzung.
- Zu jeder abgesendeten Nutzereingabe wird die zugehörige Systemantwort im selben Dialogverlauf angezeigt.

**Referenzen:** `doc/requirements/sg-001-dialogbasierte-interaktionen.md`

### Benutzbare Darstellung
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss Inhalte in der Web-GUI klar, nachvollziehbar und sitzungskonsistent darstellen.  
**Akzeptanzkriterien:**
- Dialog- und Zustandsinformationen sind für Nutzer verständlich erkennbar.
- Nutzereingaben und Systemantworten sind visuell unterscheidbar.
- Die Anzeige bleibt innerhalb einer Sitzung konsistent.

**Referenzen:** Keine

### Zugriff über Browserkontext
**Typ:** Randbedingung  
**Beschreibung:** Das System muss die Web-GUI im vorgesehenen Browserkontext bereitstellen.  
**Akzeptanzkriterien:**
- Die Oberfläche ist als Web-GUI nutzbar.
- Fachliche Interaktionen erfolgen innerhalb der Weboberfläche.

**Referenzen:** Keine

### Automatisch geoeffnete Session-Auswahl beim ersten App-Start
**Typ:** Funktional  
**Beschreibung:** Das System muss beim ersten erfolgreichen Oeffnen der Web-GUI im Browser die Session-Auswahl automatisch anzeigen, damit Nutzer NPC und Szene direkt auswaehlen koennen.  
**Akzeptanzkriterien:**
- Beim ersten erfolgreichen Laden der Web-GUI in einem Browser wird die Session-Auswahl automatisch geoeffnet.
- Die automatisch geoeffnete Session-Auswahl zeigt die Auswahlmoeglichkeiten fuer NPC und Szene an.
- Nach der ersten automatischen Oeffnung wird die Session-Auswahl bei weiteren Starts im selben Browser nicht erneut automatisch geoeffnet.
- Unabhaengig vom Erststart bleibt die Session-Auswahl weiterhin manuell aufrufbar.

**Referenzen:** Keine

### Mobile-First-Nutzung der Web-GUI
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss die Web-GUI primär für mobile Geräte in Portrait-Orientierung auslegen und die Desktop-Nutzung weiterhin vollständig unterstützen.  
**Akzeptanzkriterien:**
- Die Kerninteraktionen Lesen, Eingeben und Absenden von Dialognachrichten sind in mobiler Portrait-Orientierung ohne horizontales Scrollen nutzbar.
- Die Darstellung priorisiert auf mobilen Geräten den verfügbaren vertikalen Raum für Chat-Inhalte.
- Die Desktop-Nutzung bleibt funktional vollständig nutzbar.

**Referenzen:** Keine

### Debug-Auslieferung statischer Assets
**Typ:** Randbedingung  
**Beschreibung:** Das System muss im Debug-Betrieb statische Web-Ressourcen ohne Zwischenspeicherung bereitstellen.  
**Akzeptanzkriterien:**
- Im Debug-Betrieb werden statische Web-Ressourcen ohne Zwischenspeicherung bereitgestellt.

**Referenzen:** Keine

### Sichtbares Szenenbild und Zustandsinformationen
**Typ:** Funktional  
**Beschreibung:** Das System muss in der Web-GUI das aktuelle Szenenbild sowie sichtbare Zustandsinformationen der aktiven Sitzung bereitstellen.  
**Akzeptanzkriterien:**
- Das zur aktiven Sitzung gehörende Szenenbild wird in der Web-GUI angezeigt.
- Die Character-Beschreibung wird in der Web-GUI angezeigt.
- Die Szenenbeschreibung wird in der Web-GUI angezeigt.
- Änderungen durch Interaktionen aktualisieren Szenenbild und sichtbare Zustandsinformationen innerhalb derselben aktiven Sitzung.

**Referenzen:** `doc/requirements/sg-002-long-term-memory.md`, `doc/requirements/sg-006-dynamischer-scene-state.md`, `doc/requirements/sg-007-dreistufige-bildgenerierung.md`

### Bild-Rücksetzung über die Werkzeugleiste
**Typ:** Funktional  
**Beschreibung:** Das System muss in der Web-GUI für das aktive Sitzungsbild eine Rücksetzungsaktion bereitstellen.  
**Akzeptanzkriterien:**
- In der Web-GUI ist für das aktive Sitzungsbild eine Rücksetzungsaktion vorhanden.
- Beim Auslösen der Rücksetzungsaktion erscheint vor der Ausführung ein Bestätigungsdialog.
- Wird die Bestätigung erteilt, wird die Rücksetzung des aktiven Sitzungsbildes gemäß SG-005 ausgelöst.
- Wird die Bestätigung abgebrochen, bleibt das aktive Sitzungsbild unverändert.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`

### Bild-Löschung über die Werkzeugleiste
**Typ:** Funktional  
**Beschreibung:** Das System muss in der Web-GUI zusätzlich zur Bild-Rücksetzung eine separate Aktion bereitstellen, die nur das aktive Sitzungsbild löscht.  
**Akzeptanzkriterien:**
- In der Web-GUI ist zusätzlich zur Rücksetzungsaktion eine separate Aktion zum Löschen des aktiven Sitzungsbildes vorhanden.
- Die Löschaktion ist fachlich von der Rücksetzungsaktion getrennt und stellt kein Backup wieder her.
- Beim Auslösen der Löschaktion erscheint vor der Ausführung ein Bestätigungsdialog.
- Wird die Bestätigung erteilt, wird die Löschung des aktiven Sitzungsbildes gemäß SG-005 ausgelöst.
- Wird die Bestätigung abgebrochen, bleibt das aktive Sitzungsbild unverändert.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`

### Vergrößerbare Overlay-Ansicht des Szenenbilds auf mobilen Geräten
**Typ:** Funktional  
**Beschreibung:** Das System muss auf mobilen Geräten für das angezeigte Szenenbild eine vergrößerte Overlay-Ansicht bereitstellen.  
**Akzeptanzkriterien:**
- Nutzer können das in der Web-GUI angezeigte Szenenbild auf mobilen Geräten durch Antippen in einer Overlay-Ansicht öffnen.
- In der Overlay-Ansicht ist das Szenenbild vollständig sichtbar und wird nicht abgeschnitten.

**Referenzen:** `doc/requirements/sg-007-dreistufige-bildgenerierung.md`

### Steuerung der automatischen Bildgenerierung in der Web-GUI
**Typ:** Funktional  
**Beschreibung:** Das System muss in der Web-GUI für die aktive Sitzung eine steuerbare Einstellung zur automatischen Bildgenerierung bereitstellen.  
**Akzeptanzkriterien:**
- Für die aktive Sitzung ist im Kontext der Bildgenerierung eine Einstellung zur automatischen Bildgenerierung sichtbar.
- Wenn für die aktive Sitzung kein gespeicherter Wert vorliegt, ist die Einstellung standardmäßig aktiviert.
- Wird die automatische Bildgenerierung deaktiviert, zeigt die Web-GUI den deaktivierten Zustand eindeutig an.

**Referenzen:** `doc/requirements/sg-007-dreistufige-bildgenerierung.md`

### Sitzungspersistenz der automatischen Bildgenerierung
**Typ:** Funktional  
**Beschreibung:** Das System muss die Einstellung zur automatischen Bildgenerierung sitzungsbezogen persistieren.  
**Akzeptanzkriterien:**
- Änderungen der Einstellung werden der aktiven Sitzung zugeordnet gespeichert.
- Beim erneuten Laden der aktiven Sitzung entspricht der angezeigte Zustand der gespeicherten Einstellung.

**Referenzen:** Keine

### Manuelle Bildgenerierung trotz deaktivierter Automatik
**Typ:** Funktional  
**Beschreibung:** Das System muss die manuelle Bildgenerierung unabhängig von der Einstellung zur automatischen Bildgenerierung bereitstellen.  
**Akzeptanzkriterien:**
- `Neues Bild generieren` bleibt auch bei deaktivierter automatischer Bildgenerierung ausführbar.
- Eine manuell ausgelöste Bildgenerierung wird durch die deaktivierte automatische Bildgenerierung nicht unterdrückt.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`, `doc/requirements/sg-014-initiale-bildgenerierung-aus-npc-und-szenenkontext.md`

### Anlegen von Szenen in der Web-GUI
**Typ:** Funktional  
**Beschreibung:** Das System muss das Anlegen neuer Szenen in der Web-GUI ermöglichen.  
**Akzeptanzkriterien:**
- Eine neue Szene kann in der Web-GUI angelegt werden.
- Nach erfolgreichem Anlegen steht die neue Szene für die Nutzung in der Sitzung zur Verfügung.

**Referenzen:** `doc/requirements/sg-018-default-fallbacks-fuer-npcs-und-scenes.md`

### Steuerung der Löschung erstellter Szenen
**Typ:** Funktional  
**Beschreibung:** Das System muss in der Web-GUI eine kontrollierte Löschaktion für in der Session erstellte Szenen bereitstellen.  
**Akzeptanzkriterien:**
- Eine Löschaktion für Szenen ist in den Einstellungen vorhanden.
- Die Aktion ist nur bei erstellten Szenen ausführbar; bei Standard-Szenen ist sie deaktiviert.
- Das System zeigt den Zustand der Aktion eindeutig an (aktiv/inaktiv mit entsprechender Beschriftung).
- Vor der Ausführung wird ein Bestätigungsdialog angezeigt.
- Nach erfolgreichem Löschen wird die Session zur Standard-Szene zurückgesetzt und der Einstellungs-Panel geschlossen.

**Referenzen:** `doc/requirements/sg-020-verwaltung-dynamischer-szenen.md`
