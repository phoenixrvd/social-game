---
state: implemented
---

# SG-002: Long-Term-Memory

## Kontext
Das System verwaltet ein langfristiges Gedächtnis für relevante Informationen.  
Der fachliche Fokus liegt auf der dauerhaften Verfügbarkeit wichtiger Inhalte.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Langfristige Merkbarkeit
**Typ:** Funktional  
**Beschreibung:** Das System muss langfristig relevante Informationen speichern.  
**Akzeptanzkriterien:**
- Relevante Ereignisse können über längere Zeiträume wiederverwendet werden.
- Gespeicherte Inhalte stehen in späteren Interaktionen weiterhin zur Verfügung.

**Referenzen:** Keine

### Konsistenz des Langzeitgedächtnisses
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss langfristige Informationen widerspruchsarm halten.  
**Akzeptanzkriterien:**
- Neu hinzugefügte Inhalte widersprechen bestehenden Einträgen nicht ohne erkennbaren Anlass.
- Wiederholt abgefragte Informationen bleiben inhaltlich stabil.

**Referenzen:** Keine

### Relevanzfokus
**Typ:** Randbedingung  
**Beschreibung:** Das System muss nur langfristig relevante Inhalte im Long-Term-Memory führen.  
**Akzeptanzkriterien:**
- Kurzfristige oder nebensächliche Details werden nicht dauerhaft priorisiert.
- Langzeitinhalte sind auf die jeweilige Interaktion und Spielwelt bezogen.

**Referenzen:** Keine

