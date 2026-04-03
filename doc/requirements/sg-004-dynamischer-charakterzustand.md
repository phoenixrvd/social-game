---
state: implemented
---

# SG-004: Dynamischer Charakterzustand

## Kontext
Das System bildet den Zustand von Charakteren dynamisch ab.  
Der fachliche Fokus liegt auf veränderbaren Eigenschaften im Spielverlauf.

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

**Referenzen:** Keine

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

**Referenzen:** Keine

