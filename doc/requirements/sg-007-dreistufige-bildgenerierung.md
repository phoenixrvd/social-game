---
state: implemented
---

# SG-007: Dreistufige Bildgenerierung

## Kontext
Das System verwendet eine dreistufige Bildgenerierung.  
Der fachliche Fokus liegt auf einer strukturierten Erzeugung von Bildinhalten.

## Annahmen
- Eine dreistufige Abfolge ist fachlich vorgegeben.

## Offene Fragen
- Keine

## Anforderungen

### Dreistufiger Ablauf
**Typ:** Funktional  
**Beschreibung:** Das System muss die Bildgenerierung in drei fachlich getrennten Stufen durchführen und diese in fester Reihenfolge ausführen: (1) Kontextaufbereitung / Rohprompt-Aufbau, (2) Prompt-Optimierung, (3) Bildgenerierung und Persistierung.  
**Akzeptanzkriterien:**
- Ein Bild durchläuft immer die drei Stufen `Kontextaufbereitung / Rohprompt-Aufbau` -> `Prompt-Optimierung` -> `Bildgenerierung und Persistierung`.
- Das Ergebnis der Stufe `Kontextaufbereitung / Rohprompt-Aufbau` ist die Eingabe der Stufe `Prompt-Optimierung`.
- Das Ergebnis der Stufe `Prompt-Optimierung` ist die Eingabe der Stufe `Bildgenerierung und Persistierung`.
- Stufen werden nicht übersprungen und nicht in abweichender Reihenfolge ausgeführt.

**Referenzen:** Keine

### Stabile Ergebnisqualität über Stufen
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss über alle drei Stufen eine konsistente Bildaussage bewahren.  
**Akzeptanzkriterien:**
- Das Endbild bleibt inhaltlich mit dem Ausgangskontext vereinbar.
- Zwischenstufen führen nicht zu unbegründeten inhaltlichen Brüchen.

**Referenzen:** Keine

### Verbindliche Stufenreihenfolge
**Typ:** Randbedingung  
**Beschreibung:** Das System muss die vorgegebene Reihenfolge der drei Stufen einhalten.  
**Akzeptanzkriterien:**
- Stufen werden nicht übersprungen.
- Stufen werden nicht in abweichender Reihenfolge ausgeführt.

**Referenzen:** Keine

