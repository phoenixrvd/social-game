---
state: implemented
---

# SG-008: Zeitgesteuerte abgestimmte Fortschreibung von Szene, ETM, State und Bild

## Kontext
Das System stimmt Aktualisierungen von Szene, episodischer Erinnerung, aktuellem Charakterzustand und Bild je relevanter Interaktion aufeinander ab.  
Ziel ist ein gemeinsames, fachlich stimmiges Ergebnis über diese Bereiche hinweg.

## Annahmen
- Die fachliche Fortschreibung wird zeitgesteuert durch den Scheduler ausgelöst.
- LLM-Tool-/Function-Calling wird dafür nicht verwendet.

## Offene Fragen
- Keine

## Anforderungen

### Abgestimmte Fortschreibung mehrerer Bereiche
**Typ:** Funktional  
**Beschreibung:** Das System muss die betroffenen Bereiche Szene, episodische Erinnerung, aktueller Charakterzustand und Bild in einem abgestimmten, zeitgesteuerten Gesamtvorgang fortschreiben.  
**Akzeptanzkriterien:**
- Für eine relevante Interaktion werden alle fachlich betroffenen Bereiche im selben Gesamtzusammenhang zeitnah aktualisiert.
- Die Fortschreibung ist als zusammengehöriger fachlicher Ablauf nachvollziehbar.

**Referenzen:** `doc/adr/003-synchroner-update-orchestrator.md`

### Nachrichtengetriggerte Hintergrundfortschreibung
**Typ:** Funktional  
**Beschreibung:** Das System muss fachliche Hintergrundjobs nur dann zur Ausführung vormerken, wenn eine neue final verarbeitete Chat-Nachricht vorliegt.  
**Akzeptanzkriterien:**
- Ohne neue final verarbeitete Chat-Nachricht wird kein fachlicher Hintergrundjob neu ausgelöst.
- Mehrere Scheduler-Zyklen ohne neue Nachricht führen zu keinem zusätzlichen Job-Lauf.
- Nach einer neuen final verarbeiteten Chat-Nachricht werden die fachlichen Hintergrundjobs für den nächsten Scheduler-Zyklus vorgemerkt.

**Referenzen:** `doc/requirements/sg-001-dialogbasierte-interaktionen.md`, `doc/adr/003-synchroner-update-orchestrator.md`

### Bereinigung vorgemerkter Jobs bei Reset aktiver Laufzeitdaten
**Typ:** Funktional  
**Beschreibung:** Das System muss beim Zurücksetzen der aktiven NPC-Laufzeitdaten alle vorgemerkten fachlichen Hintergrundjobs verwerfen, damit keine Jobs mit veraltetem Kontext ausgeführt werden.  
**Akzeptanzkriterien:**
- Wird die Rücksetzung der aktiven NPC-Laufzeitdaten ausgelöst, werden alle zu diesem Zeitpunkt vorgemerkten fachlichen Hintergrundjobs vor Abschluss der Rücksetzung entfernt.
- Nach der Rücksetzung wird kein vor dem Reset vorgemerkter fachlicher Hintergrundjob mehr ausgeführt.
- Eine erneute fachliche Hintergrundfortschreibung erfolgt erst nach einer neuen final verarbeiteten Chat-Nachricht.

**Referenzen:** `doc/requirements/sg-001-dialogbasierte-interaktionen.md`, `doc/adr/003-synchroner-update-orchestrator.md`

### Rate-limitierte Job-Ausführung
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss jeden fachlichen Hintergrundjob innerhalb seines definierten Rate-Limits ausführen.  
**Akzeptanzkriterien:**
- Zwischen zwei Läufen desselben Jobs wird das definierte Rate-Limit eingehalten.
- Ein Scheduler-Zyklus darf keinen Job-Lauf erzwingen, wenn dessen Rate-Limit noch nicht abgelaufen ist.
- Ein Job bleibt vorgemerkt, bis seine Ausführung unter Einhaltung des Rate-Limits möglich ist.

**Referenzen:** `doc/adr/003-synchroner-update-orchestrator.md`

### Bereichsübergreifende Konsistenz
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss Ergebnisse der aktualisierten Bereiche inhaltlich aufeinander abstimmen, ohne dafür die Antwortgenerierung des LLM an Tool-/Function-Calling zu koppeln.  
**Akzeptanzkriterien:**
- Änderungen an Szene, episodischer Erinnerung, aktuellem Charakterzustand und Bild widersprechen sich nicht ohne fachlichen Anlass.
- Bereichsübergreifende Bezüge bleiben in einer Interaktion konsistent.
- Die Fortschreibung benötigt kein Twice-Call-Pattern für getrennte Antwort- und Tool-Läufe.

**Referenzen:** `doc/requirements/sg-015-episodic-term-memory.md`

### Geltungsbereich der Orchestrierung
**Typ:** Randbedingung  
**Beschreibung:** Das System muss die zeitgesteuerte, abgestimmte Fortschreibung auf Szene, episodische Erinnerung, aktuellen Charakterzustand und Bild beschränken.  
**Akzeptanzkriterien:**
- Nur diese vier Bereiche sind Teil der abgestimmten Fortschreibung.
- Andere Bereiche werden dabei nicht einbezogen.

**Referenzen:** `doc/requirements/sg-002-long-term-memory.md`, `doc/requirements/sg-004-dynamischer-charakterzustand.md`, `doc/requirements/sg-006-dynamischer-scene-state.md`, `doc/requirements/sg-015-episodic-term-memory.md`
