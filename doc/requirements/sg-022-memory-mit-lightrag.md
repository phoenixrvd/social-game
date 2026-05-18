---
state: implemented
---

# SG-022: Memory mit LightRAG

## Kontext
Die Memory-Funktion nutzt LightRAG fuer ETM-Speicherung und ETM-Retrieval.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### ETM-Speicherung und Retrieval über LightRAG
**Typ:** Funktional  
**Beschreibung:** Das System muss ETM-Episoden über LightRAG pro aktiver Spielinstanz speichern und vor einer NPC-Antwort relevante frühere Episoden aus dem aktiven Kontext abrufen können.  
**Akzeptanzkriterien:**
- ETM-Episoden werden im aktiven NPC- und Szenenkontext abgelegt.
- Episoden anderer NPCs oder Szenen werden nicht im selben Retrieval-Kontext verwendet.
- Die aktuelle User-Nachricht kann als primäre Retrieval-Query genutzt werden.
- Ohne passende Episoden wird kein zusätzlicher Erinnerungsinhalt ergänzt.
- Abgerufene Episoden ergänzen den aktuellen Gesprächskontext, ersetzen ihn aber nicht.

**Referenzen:** `doc/requirements/sg-015-episodic-term-memory.md`, `doc/requirements/sg-003-short-term-memory.md`
