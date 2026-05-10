---
state: defined
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

### Automatisch geöffnete Session-Auswahl beim ersten App-Start
**Typ:** Funktional  
**Beschreibung:** Das System muss beim ersten erfolgreichen Öffnen der Web-GUI im Browser die Session-Auswahl automatisch anzeigen, damit Nutzer NPC und Szene direkt auswählen können.  
**Akzeptanzkriterien:**
- Beim ersten erfolgreichen Laden der Web-GUI in einem Browser wird die Session-Auswahl automatisch geöffnet.
- Die automatisch geöffnete Session-Auswahl zeigt die Auswahlmöglichkeiten für NPC und Szene an.
- Nach der ersten automatischen Öffnung wird die Session-Auswahl bei weiteren Starts im selben Browser nicht erneut automatisch geöffnet.
- Unabhängig vom Erststart bleibt die Session-Auswahl weiterhin manuell aufrufbar.

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
- Die Auslöseaktion für das Anlegen heißt `Erstellen`.
- Die Web-GUI bietet beim Erstellen die Optionen `Scene Erstellen` und `NPC Kontext erstellen` an.
- Beide Optionen sind standardmäßig aktiviert.
- Die Erstellung ist nur ausführbar, wenn eine Beschreibung vorhanden ist und mindestens eine der beiden Optionen aktiviert ist.
- Nach erfolgreichem Anlegen steht die neue Szene für die Nutzung in der Sitzung zur Verfügung.

**Referenzen:** `doc/requirements/sg-018-default-fallbacks-fuer-npcs-und-scenes.md`

### Anlegen von NPCs in der Web-GUI
**Typ:** Funktional  
**Beschreibung:** Das System muss das Anlegen neuer NPCs in der Web-GUI ermöglichen.  
**Akzeptanzkriterien:**
- Eine neue NPC-Erstellung kann in der Web-GUI aus demselben fachlichen Kontext wie die Szenen-Erstellung gestartet werden.
- Für die NPC-Erstellung kann eine Beschreibung eingegeben und abgesendet werden.
- Nach erfolgreichem Anlegen steht der neue NPC für die Nutzung in der Sitzung zur Verfügung.
- Die Oberfläche zeigt Erfolg oder Fehlschlag des Anlegens nachvollziehbar an.

**Referenzen:** `doc/requirements/sg-018-default-fallbacks-fuer-npcs-und-scenes.md`

### Optionale Löschung erstellter Inhalte beim Verlauf-Löschen
**Typ:** Funktional  
**Beschreibung:** Das System muss die optionale Löschung erstellter NPCs, Szenen und NPC-Kontexte in der Web-GUI über die Aktion `Verlauf löschen` bereitstellen.  
**Akzeptanzkriterien:**
- In der Web-GUI gibt es keinen separaten Button `Verlauf und Szene löschen`.
- Unter `Verlauf löschen` werden die Checkboxen `Erstellten NPC mit löschen`, `Erstellte Szene mit löschen` und `Erstellten NPC-Kontext löschen` angezeigt.
- Vor der Ausführung kann für die Löschoptionen entschieden werden, ob sie berücksichtigt werden sollen.
- Wird `Erstellten NPC mit löschen` aktiviert, wird `Erstellten NPC-Kontext löschen` automatisch aktiviert und ist nicht separat änderbar.

**Referenzen:** `doc/requirements/sg-009-git-basierte-spielstandshistorie.md`, `doc/requirements/sg-018-default-fallbacks-fuer-npcs-und-scenes.md`

### Aktivierbarkeit der optionalen Löschoptionen
**Typ:** Funktional  
**Beschreibung:** Das System muss die optionalen Löschoptionen nur bei passend erstellten aktiven Inhalten aktivierbar machen.  
**Akzeptanzkriterien:**
- `Erstellten NPC mit löschen` ist nur aktivierbar, wenn der aktive NPC erstellt oder dynamisch und nicht der Default-NPC ist.
- `Erstellte Szene mit löschen` ist nur aktivierbar, wenn die aktive Szene erstellt oder dynamisch und nicht die Default-Szene ist.
- `Erstellten NPC-Kontext löschen` bleibt auch dann aktivierbar, wenn `Erstellten NPC mit löschen` nicht aktivierbar ist.
- Sind die Voraussetzungen für NPC- oder Szenenlöschung nicht erfüllt, ist die jeweilige Checkbox deaktiviert.

**Referenzen:** `doc/requirements/sg-018-default-fallbacks-fuer-npcs-und-scenes.md`

### Dynamischer Bestätigungsdialog beim Verlauf-Löschen
**Typ:** Funktional  
**Beschreibung:** Das System muss vor dem Verlauf-Löschen die tatsächlich ausgewählten Löschumfänge verständlich bestätigen lassen.  
**Akzeptanzkriterien:**
- Vor der Ausführung von `Verlauf löschen` erscheint ein Bestätigungsdialog.
- Der Bestätigungsdialog verwendet die Einleitung `Sollen folgende Dinge gelöscht werden?`.
- Der Bestätigungsdialog zählt genau die Inhalte auf, die mit der aktuellen Auswahl gelöscht werden.
- Wird die Bestätigung abgebrochen, bleiben Verlauf und ausgewählte Inhalte unverändert.

**Referenzen:** `doc/requirements/sg-009-git-basierte-spielstandshistorie.md`, `doc/requirements/sg-018-default-fallbacks-fuer-npcs-und-scenes.md`
