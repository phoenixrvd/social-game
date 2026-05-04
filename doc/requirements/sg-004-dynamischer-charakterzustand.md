---
state: implemented
---

# SG-004: Dynamischer Charakterzustand

## Kontext
Das System bildet den Zustand von Charakteren dynamisch ab.  
Der fachliche Fokus liegt auf veränderbaren Eigenschaften im Spielverlauf.
Charakterzustand ist eine abgeleitete Sicht auf aktuelle und erinnerte Ereignisse.
Der Beziehungskontext ist Bestandteil von `state.md`.

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
**Beschreibung:** Das System muss Charakterzustände innerhalb des fachlichen Spielkontexts ausschließlich über `state.md` führen.  
**Akzeptanzkriterien:**
- Zustandsinformationen bleiben auf spielrelevante Merkmale begrenzt.
- Zustände werden nicht losgelöst von der laufenden Handlung interpretiert.
- Für die aktive Spielinstanz wird ausschließlich `state.md` als Zustandsquelle verwendet.
- Ein separater Beziehungskontext außerhalb von `state.md` wird fachlich nicht verwendet.

**Referenzen:** `doc/requirements/sg-015-episodic-term-memory.md`
