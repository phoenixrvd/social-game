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

### Zentrale Definition gemeinsamer Bild-Style-Regeln
**Typ:** Funktional  
**Beschreibung:** Das System muss gemeinsame Bild-Style-Regeln in einem separaten Prompt-Template zentral definieren.  
**Akzeptanzkriterien:**
- Für gemeinsame Bild-Style-Regeln existiert ein separates Prompt-Template.
- Gemeinsame Bild-Style-Regeln sind nicht ausschließlich in genau einem der Bild-Prompts `Build`, `Refresh` oder `Scene-Merge` definiert.

**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Einheitliche Nutzung des zentralen Bild-Style-Templates
**Typ:** Funktional  
**Beschreibung:** Das System muss das separate Prompt-Template mit gemeinsamen Bild-Style-Regeln in den Bild-Prompts `Build`, `Refresh` und `Scene-Merge` verwenden.  
**Akzeptanzkriterien:**
- Der Bild-Prompt `Build` verwendet das separate Prompt-Template mit gemeinsamen Bild-Style-Regeln.
- Der Bild-Prompt `Refresh` verwendet das separate Prompt-Template mit gemeinsamen Bild-Style-Regeln.
- Der Bild-Prompt `Scene-Merge` verwendet das separate Prompt-Template mit gemeinsamen Bild-Style-Regeln.
- Eine Änderung am separaten Prompt-Template wirkt auf die gemeinsamen Bild-Style-Regeln aller drei Bild-Prompts.

**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

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
