---
state: implemented
---

# SG-008: LLM-based Update-Orchestrator für Szene, ETM, State und Bild

## Kontext
Das System koordiniert Aktualisierungen für Szene, ETM, State und Bild in einem Orchestrator.  
Der fachliche Fokus liegt auf abgestimmten Aktualisierungen dieser Bereiche.

## Annahmen
- Der Orchestrator nutzt ein LLM als fachliche Grundlage der Koordination.

## Offene Fragen
- Keine

## Anforderungen

### Orchestrierte Aktualisierung mehrerer Bereiche
**Typ:** Funktional  
**Beschreibung:** Das System muss Aktualisierungen von Szene, ETM, State und Bild koordiniert ausführen.  
**Akzeptanzkriterien:**
- Für eine relevante Interaktion werden alle vorgesehenen Bereiche im Zusammenhang aktualisiert.
- Aktualisierungen sind als zusammengehöriger Ablauf nachvollziehbar.

**Referenzen:** Keine

### Bereichsübergreifende Konsistenz
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss Ergebnisse der aktualisierten Bereiche inhaltlich aufeinander abstimmen.  
**Akzeptanzkriterien:**
- Änderungen in Szene, ETM, State und Bild widersprechen sich nicht ohne fachlichen Anlass.
- Bereichsübergreifende Bezüge bleiben in einer Interaktion konsistent.

**Referenzen:** `doc/requirements/sg-015-episodic-term-memory.md`

### Geltungsbereich der Orchestrierung
**Typ:** Randbedingung  
**Beschreibung:** Das System muss die Orchestrierung auf Szene, ETM, State und Bild beschränken.  
**Akzeptanzkriterien:**
- Der Orchestrator verarbeitet nur die definierten Zielbereiche.
- Nicht definierte Bereiche werden nicht Teil des orchestrierten Update-Ablaufs.

**Referenzen:** `doc/requirements/sg-002-long-term-memory.md`, `doc/requirements/sg-004-dynamischer-charakterzustand.md`, `doc/requirements/sg-006-dynamischer-scene-state.md`, `doc/requirements/sg-015-episodic-term-memory.md`
