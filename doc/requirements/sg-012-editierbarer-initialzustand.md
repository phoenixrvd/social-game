---
state: defined
---

# SG-012: Editierbarer Initialzustand

## Kontext
In der Web-GUI können die initialen Zustände einer aktiven Sitzung vor der ersten Nachricht bearbeitet werden.
SG-012 beschreibt nur Platzierung, Bearbeitungsablauf und Betriebsverhalten dieser Bearbeitung; fachliche Zustände und allgemeine UI-Grundsätze werden referenziert.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Platzierung der editierbaren Bereiche
**Typ:** Funktional  
**Beschreibung:** Das System muss Scene-State und Charakterzustand direkt im Context-Bereich sowie den statischen Beziehungs-Initialkontext im Panel unter der Session-Auswahl bearbeitbar bereitstellen.  
**Akzeptanzkriterien:**
- Die Bearbeitung von Scene-State erfolgt im Context-Bereich.
- Die Bearbeitung des Charakterzustands erfolgt im Context-Bereich.
- Die Bearbeitung von `relationship.md` erfolgt im Panel unter der Session-Auswahl.
**Referenzen:** `doc/requirements/sg-011-web-gui.md`, `doc/adr/007-ui-architektur-mit-web-components.md`

### Icon-Aktionen für die Bearbeitung
**Typ:** Funktional  
**Beschreibung:** Das System muss die Aktionen Bearbeiten, Speichern, Revert und Schließen als Icon-Aktionen bereitstellen.  
**Akzeptanzkriterien:**
- Bearbeiten wird als Icon-Aktion dargestellt.
- Speichern wird als Icon-Aktion dargestellt.
- Revert wird als Icon-Aktion dargestellt.
- Schließen wird als Icon-Aktion dargestellt.
**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Sichtbarkeit der Revert-Aktion
**Typ:** Funktional  
**Beschreibung:** Das System muss die Revert-Aktion nur im Bearbeitungsmodus des betroffenen Bereichs anzeigen.  
**Akzeptanzkriterien:**
- Außerhalb des Bearbeitungsmodus ist für den betroffenen Bereich keine Revert-Aktion sichtbar.
- Im Bearbeitungsmodus ist für den betroffenen Bereich eine Revert-Aktion sichtbar.
**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Bestätigung vor Revert bei ungespeicherten Änderungen
**Typ:** Funktional  
**Beschreibung:** Das System muss vor einem Revert ungespeicherter Änderungen eine Bestätigung verlangen.  
**Akzeptanzkriterien:**
- Wenn der betroffene Bereich ungespeicherte Änderungen enthält, erscheint vor dem Revert ein Bestätigungsdialog.
- Ohne Bestätigung bleibt der bearbeitete Inhalt unverändert.
**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Ende des Bearbeitungsmodus nach Speichern
**Typ:** Funktional  
**Beschreibung:** Das System muss den Bearbeitungsmodus des betroffenen Bereichs nach erfolgreichem Speichern beenden.  
**Akzeptanzkriterien:**
- Nach erfolgreichem Speichern ist der betroffene Bereich nicht mehr im Bearbeitungsmodus.
**Referenzen:** `doc/requirements/sg-002-long-term-memory.md`, `doc/requirements/sg-004-dynamischer-charakterzustand.md`, `doc/requirements/sg-006-dynamischer-scene-state.md`

### Ende des Bearbeitungsmodus nach Revert
**Typ:** Funktional  
**Beschreibung:** Das System muss nach einem Revert den Text des betroffenen Bereichs auf den Initialzustand zurücksetzen und den Bearbeitungsmodus beibehalten.
**Akzeptanzkriterien:**
- Nach einem Revert entspricht der Text des betroffenen Bereichs dem Initialzustand.
- Nach einem Revert bleibt der betroffene Bereich im Bearbeitungsmodus.
**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Zustandswahrung bei Fehlern
**Typ:** Funktional  
**Beschreibung:** Das System muss bei Fehlern den zuletzt erfolgreich gespeicherten Zustand wahren.  
**Akzeptanzkriterien:**
- Bei einem Fehler bleiben bereits erfolgreich gespeicherte Zustände unverändert.
**Referenzen:** `doc/requirements/sg-002-long-term-memory.md`, `doc/requirements/sg-004-dynamischer-charakterzustand.md`, `doc/requirements/sg-006-dynamischer-scene-state.md`

### Generische Fehlerhinweise
**Typ:** Funktional  
**Beschreibung:** Das System muss bei Fehlern generische Fehlerhinweise ohne Ursachenoffenlegung anzeigen.  
**Akzeptanzkriterien:**
- Bei einem Fehler wird ein generischer Fehlerhinweis angezeigt.
- Der Fehlerhinweis legt keine Ursache offen.
**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Mobile-stabile Editfelder
**Typ:** Nicht-funktional  
**Beschreibung:** Das System darf auf Mobile beim Tippen in Editfelder keinen Positionssprung verursachen.  
**Akzeptanzkriterien:**
- Beim Fokussieren eines Editfelds bleibt die Position des betroffenen Bereichs stabil.
- Mehrzeilige Editfelder wachsen in der Höhe statt eine innere Scrollbar zu verwenden.
**Referenzen:** `doc/requirements/sg-011-web-gui.md`
