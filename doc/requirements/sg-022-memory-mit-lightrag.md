---
state: draft
---

# SG-022: Memory mit LightRAG

## Kontext
Die Memory-Funktion nutzt LightRAG als gemeinsame RAG-Basis fuer ETM und Faktenextraktion.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### ETM-Retrieval über LightRAG
**Typ:** Funktional  
**Beschreibung:** Das System muss vor einer NPC-Antwort relevante frühere Episoden über LightRAG aus dem aktiven Kontext abrufen können.  
**Akzeptanzkriterien:**
- Die aktuelle User-Nachricht kann als primäre Retrieval-Query genutzt werden.
- Ohne passende Episoden wird kein zusätzlicher Erinnerungsinhalt ergänzt.
- Abgerufene Episoden ergänzen den aktuellen Gesprächskontext, ersetzen ihn aber nicht.

**Referenzen:** `doc/requirements/sg-015-episodic-term-memory.md`, `doc/requirements/sg-003-short-term-memory.md`

### Faktenextraktion über RAG
**Typ:** Funktional  
**Beschreibung:** Das System muss relevante Fakten für den aktuellen Kontext über LightRAG aus verfügbaren Memory-Quellen ableiten können.  
**Akzeptanzkriterien:**
- Relevante Fakten können aus ETM-Inhalten abgeleitet werden.
- Ohne passenden Faktenkontext werden keine sicheren Fakten ergänzt.

**Referenzen:** `doc/requirements/sg-015-episodic-term-memory.md`

### Unveränderte Modelllandschaft
**Typ:** Randbedingung  
**Beschreibung:** Das System muss mit LightRAG dieselben Modelle wie bisher verwenden.  
**Akzeptanzkriterien:**
- Das konfigurierte LLM-Setup bleibt unverändert.
- Das konfigurierte Embedding-Modell bleibt unverändert.

**Referenzen:** `doc/adr/004-modellstrategie.md`
