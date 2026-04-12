---
state: implemented
---

# SG-006: Dynamischer Scene-State

## Kontext
Das System verwaltet einen dynamischen Zustand von Szenen.  
Der fachliche Fokus liegt auf Veränderungen innerhalb der Spielumgebung.
Scene-State ist eine abgeleitete Sicht auf die aktive Situation und kann durch relevante Erinnerungen informiert werden.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Aktualisierung des Szenenzustands
**Typ:** Funktional  
**Beschreibung:** Das System muss den Zustand einer Szene anhand relevanter Ereignisse aktualisieren.  
**Akzeptanzkriterien:**
- Ereignisse in der Szene führen zu nachvollziehbaren Zustandsänderungen.
- Der aktuelle Szenenzustand steht für nachfolgende Interaktionen zur Verfügung.
- Relevante ETM-Erinnerungen können bei der Aktualisierung des aktuellen Szenenzustands berücksichtigt werden.

**Referenzen:** `doc/requirements/sg-015-episodic-term-memory.md`

### Konsistenter Szenenkontext
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss den Szenenzustand widerspruchsarm führen.  
**Akzeptanzkriterien:**
- Neue Zustände widersprechen dem bisherigen Szenenverlauf nicht ohne erkennbare Ursache.
- Interaktionen beziehen sich auf denselben aktuellen Szenenzustand.

**Referenzen:** Keine

### Begrenzung auf szenenrelevante Inhalte
**Typ:** Randbedingung  
**Beschreibung:** Das System muss den Scene-State auf Inhalte der jeweiligen Szene begrenzen.  
**Akzeptanzkriterien:**
- Szenenfremde Informationen werden nicht als Teil des Scene-State behandelt.
- Der Scene-State bleibt an die aktive Szene gebunden.
- Scene-State wird nicht automatisch als separates Memory-Artefakt persistiert.

**Referenzen:** `doc/requirements/sg-002-long-term-memory.md`, `doc/requirements/sg-015-episodic-term-memory.md`
