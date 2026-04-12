---
state: removed
---

# SG-002: Long-Term-Memory (entfernt)

## Kontext
Die dedizierte Long-Term-Memory-Funktion wurde aus dem System entfernt.
Frühere Gesprächsinhalte werden über Episodic Term Memory (ETM) als abrufbare Episoden geführt.
Die initiale Beziehungsgrundlage liegt statisch in `npcs/<npc_id>/relationship.md` und wird beim ersten Laden an den initialen Charakterzustand angehängt.
Ein separates LTM-Artefakt ist dafür fachlich nicht mehr notwendig.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Kein separates Long-Term-Memory-Artefakt
**Typ:** Funktional  
**Beschreibung:** Das System führt kein eigenes LTM-Dateiartefakt mehr.  
**Akzeptanzkriterien:**
- Es gibt kein fachlich verwendetes `ltm.md` mehr.
- Frühere abrufbare Erinnerungen werden über ETM geladen.
- Initiale Beziehungsgrundlagen werden über `relationship.md` in den initialen State eingebracht.

**Referenzen:** `doc/requirements/sg-004-dynamischer-charakterzustand.md`, `doc/requirements/sg-015-episodic-term-memory.md`
