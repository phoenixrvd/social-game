---
state: implemented
---

# SG-008: LLM-based Update-Orchestrator für Szene, LTM und Bild

## Kontext
Das System koordiniert Aktualisierungen für Szene, Long-Term-Memory und Bild in einem Orchestrator.  
Der fachliche Fokus liegt auf abgestimmten Aktualisierungen dieser Bereiche.

## Annahmen
- Der Orchestrator nutzt ein LLM als fachliche Grundlage der Koordination.

## Offene Fragen
- Keine

## Anforderungen

### Orchestrierte Aktualisierung mehrerer Bereiche
**Typ:** Funktional  
**Beschreibung:** Das System muss Aktualisierungen von Szene, Long-Term-Memory und Bild koordiniert ausführen.  
**Akzeptanzkriterien:**
- Für eine relevante Interaktion werden alle vorgesehenen Bereiche im Zusammenhang aktualisiert.
- Aktualisierungen sind als zusammengehöriger Ablauf nachvollziehbar.

**Referenzen:** Keine

### Bereichsübergreifende Konsistenz
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss Ergebnisse der aktualisierten Bereiche inhaltlich aufeinander abstimmen.  
**Akzeptanzkriterien:**
- Änderungen in Szene, Long-Term-Memory und Bild widersprechen sich nicht ohne fachlichen Anlass.
- Bereichsübergreifende Bezüge bleiben in einer Interaktion konsistent.

**Referenzen:** Keine

### Geltungsbereich der Orchestrierung
**Typ:** Randbedingung  
**Beschreibung:** Das System muss die Orchestrierung auf Szene, Long-Term-Memory und Bild beschränken.  
**Akzeptanzkriterien:**
- Der Orchestrator verarbeitet nur die definierten Zielbereiche.
- Nicht definierte Bereiche werden nicht Teil des orchestrierten Update-Ablaufs.

**Referenzen:** Keine

