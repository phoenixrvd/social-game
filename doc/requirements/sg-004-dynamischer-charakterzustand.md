---
state: implemented
---

# SG-004: Dynamischer Charakterzustand

## Kontext
Das System bildet den Zustand von Charakteren dynamisch ab.  
Der fachliche Fokus liegt auf veränderbaren Eigenschaften im Spielverlauf.
Charakterzustand ist eine abgeleitete Sicht auf aktuelle und erinnerte Ereignisse.
Der initiale Zustandskontext kann zusätzlich aus einer statischen Beziehungsgrundlage stammen.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Zustandsänderungen von Charakteren
**Typ:** Funktional  
**Beschreibung:** Das System muss Änderungen am Charakterzustand im Verlauf von Interaktionen berücksichtigen.  
**Akzeptanzkriterien:**
- Charakterzustände können sich nach relevanten Ereignissen ändern.
- Spätere Interaktionen beziehen den aktuellen Zustand ein.
- Relevante ETM-Erinnerungen können bei der Ermittlung des aktuellen Charakterzustands berücksichtigt werden.

**Referenzen:** `doc/requirements/sg-015-episodic-term-memory.md`

### Kohärenz des Charakterverhaltens
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss das Verhalten von Charakteren konsistent zum aktuellen Zustand halten.  
**Akzeptanzkriterien:**
- Reaktionen eines Charakters passen zum dokumentierten Zustand.
- Unbegründete Zustandswechsel treten nicht auf.

**Referenzen:** Keine

### Zustand im Spielkontext
**Typ:** Randbedingung  
**Beschreibung:** Das System muss Charakterzustände innerhalb des fachlichen Spielkontexts führen.  
**Akzeptanzkriterien:**
- Zustandsinformationen bleiben auf spielrelevante Merkmale begrenzt.
- Zustände werden nicht losgelöst von der laufenden Handlung interpretiert.
- Wenn noch keine Laufzeit-`state.md` für die aktive Spielinstanz existiert, wird `npcs/<npc_id>/relationship.md` an den initial geladenen Zustand angehängt.
- Sobald eine Laufzeit-`state.md` existiert, ersetzt diese den initial kombinierten Zustand vollständig.
- `relationship.md` ist nur initialer Kontext und kein separates Laufzeitgedächtnis.

**Referenzen:** `doc/requirements/sg-002-long-term-memory.md`, `doc/requirements/sg-015-episodic-term-memory.md`
