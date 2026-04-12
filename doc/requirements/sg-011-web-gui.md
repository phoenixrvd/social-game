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

**Technische Anmerkung:** Beim initialen Laden eines Nachrichtenverlaufs (leere Nachrichtenliste vor dem Render) wird ohne Scroll-Animation direkt ans Ende gescrollt (`scrollBehavior: instant`), um unnötige Animationen beim Bulk-Insert zu vermeiden. Inkrementelle Updates (z. B. gestreamte Chunks) verwenden weiche Scroll-Animation (`scrollBehavior: smooth`).

**Referenzen:** Keine

### Zugriff über Browserkontext
**Typ:** Randbedingung  
**Beschreibung:** Das System muss die Web-GUI im vorgesehenen Browserkontext bereitstellen.  
**Akzeptanzkriterien:**
- Die Oberfläche ist als Web-GUI nutzbar.
- Fachliche Interaktionen erfolgen innerhalb der Weboberfläche.

**Referenzen:** Keine

### Debug-Auslieferung statischer Assets
**Typ:** Randbedingung  
**Beschreibung:** Das System muss bei aktiviertem `WEB_DEBUG` statische Assets ohne Caching ausliefern.  
**Akzeptanzkriterien:**
- Bei aktiviertem `WEB_DEBUG` werden statische Assets ohne Caching ausgeliefert.

**Referenzen:** Keine

### Sichtbares Szenenbild und Zustandsinformationen
**Typ:** Funktional  
**Beschreibung:** Das System muss in der Web-GUI das aktuelle Szenenbild sowie sichtbare Zustandsinformationen der aktiven Sitzung bereitstellen.  
**Akzeptanzkriterien:**
- Das zur aktiven Sitzung gehörende Szenenbild wird in der Web-GUI angezeigt.
- Die Character-Beschreibung wird in der Web-GUI angezeigt.
- Die Scene-Beschreibung wird in der Web-GUI angezeigt.
- Änderungen durch Interaktionen aktualisieren Szenenbild und sichtbare Zustandsinformationen innerhalb derselben aktiven Sitzung.


**Referenzen:** `doc/requirements/sg-002-long-term-memory.md`, `doc/requirements/sg-006-dynamischer-scene-state.md`, `doc/requirements/sg-007-dreistufige-bildgenerierung.md`

### Vergrößerbare Overlay-Ansicht des Szenenbilds auf mobilen Geräten
**Typ:** Funktional  
**Beschreibung:** Das System muss auf mobilen Geräten für das angezeigte Szenenbild eine vergrößerte Overlay-Ansicht ohne Beschneidung bereitstellen.  
**Akzeptanzkriterien:**
- Nutzer können das in der Web-GUI angezeigte Szenenbild auf mobilen Geräten durch Antippen in einer Overlay-Ansicht öffnen.
- In der Overlay-Ansicht ist das Szenenbild vollständig sichtbar und wird nicht abgeschnitten.
- Die Overlay-Ansicht zeigt das Szenenbild zentriert und unabhängig vom Seitenverhältnis ohne Beschneidung an.

**Referenzen:** `doc/requirements/sg-007-dreistufige-bildgenerierung.md`
