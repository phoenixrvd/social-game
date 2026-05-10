---
state: implemented
---

# SG-016: Overrides-Verzeichnis

## Kontext
Das System trennt versionierte Quelldaten, lokale Überschreibungen und Laufzeitdaten.
SG-016 beschreibt ausschließlich die fachliche Rolle des lokalen Verzeichnisses `.overrides/`; allgemeine Datentrennung und Pfadauflösung werden referenziert.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Überschreiben des NPC-Initialzustands
**Typ:** Funktional  
**Beschreibung:** Das System muss den Initialzustand eines NPC über gleichnamige Dateien unter `.overrides/npcs/<npc_id>/` vollständig überschreibbar machen.  
**Akzeptanzkriterien:**
- Jede Datei unter `npcs/<npc_id>/` kann durch eine gleichnamige Datei unter `.overrides/npcs/<npc_id>/` vollständig ersetzt werden.
- Ohne lokale Überschreibung bleibt der versionierte Standardinhalt unter `npcs/<npc_id>/` wirksam.
**Referenzen:** `engine/config.py`, `engine/storage.py`

### Hinzufügen eigener NPCs über Overrides
**Typ:** Funktional  
**Beschreibung:** Das System muss NPCs, die ausschließlich unter `.overrides/npcs/` existieren, wie Standard-NPCs behandeln.  
**Akzeptanzkriterien:**
- Ein NPC ohne Gegenstück unter `npcs/` kann ausschließlich unter `.overrides/npcs/<npc_id>/` bereitgestellt werden.
- Solche NPCs erscheinen in der NPC-Liste gemeinsam mit den Standard-NPCs.
- Solche NPCs sind im fachlichen Verhalten gegenüber Standard-NPCs gleichgestellt.
**Referenzen:** `engine/storage.py`

### Überschreiben von Szenendaten
**Typ:** Funktional  
**Beschreibung:** Das System muss Szenendaten über gleichnamige Dateien unter `.overrides/scenes/<scene_id>/` vollständig überschreibbar machen.  
**Akzeptanzkriterien:**
- Jede Datei unter `scenes/<scene_id>/` kann durch eine gleichnamige Datei unter `.overrides/scenes/<scene_id>/` vollständig ersetzt werden.
- Ohne lokale Überschreibung bleibt der versionierte Standardinhalt unter `scenes/<scene_id>/` wirksam.
**Referenzen:** `engine/config.py`, `engine/storage.py`

### NPC-szenenspezifische Ergänzungen über Overrides
**Typ:** Funktional  
**Beschreibung:** Das System muss NPC-szenenspezifische Ergänzungen über gleichnamige Dateien unter `.overrides/npcs/<npc_id>/scenes/<scene_id>/` vollständig überschreibbar machen.  
**Akzeptanzkriterien:**
- Jede Datei unter `npcs/<npc_id>/scenes/<scene_id>/` kann durch eine gleichnamige Datei unter `.overrides/npcs/<npc_id>/scenes/<scene_id>/` vollständig ersetzt werden.
- Ohne lokale Überschreibung bleibt der versionierte Standardinhalt wirksam.
- Fehlt eine eigene NPC-szenenspezifische Ergänzung, kann ein passend auf den aktiven NPC bezogener Default-Fallback wirksam werden.
**Referenzen:** `engine/storage.py`

### Entfernen lokaler NPC-szenenspezifischer Ergänzungen
**Typ:** Funktional  
**Beschreibung:** Das System muss lokal erzeugte NPC-szenenspezifische Ergänzungen getrennt von NPC und Scene entfernbar machen.  
**Akzeptanzkriterien:**
- Eine lokal erzeugte NPC-szenenspezifische Ergänzung kann entfernt werden, ohne den betroffenen NPC oder die betroffene Scene zu löschen.
- Nach dem Entfernen wirkt die lokale NPC-szenenspezifische Ergänzung nicht mehr.
- Danach greifen für den betroffenen NPC in der betroffenen Scene wieder die verbleibenden Prioritäten und Fallbacks.
**Referenzen:** `doc/requirements/sg-018-default-fallbacks-fuer-npcs-und-scenes.md`

### Priorisierung der Datenschichten
**Typ:** Randbedingung  
**Beschreibung:** Das System muss lokale Überschreibungen gegenüber versionierten Standarddaten priorisieren, aber hinter Laufzeitdaten einordnen.  
**Akzeptanzkriterien:**
- Wenn für denselben Inhalt Laufzeitdaten, lokale Überschreibung und versionierter Standard vorliegen, gilt die Reihenfolge Laufzeitdaten vor lokaler Überschreibung vor versioniertem Standard.
- Wenn keine Laufzeitdaten vorliegen, gilt die Reihenfolge lokale Überschreibung vor versioniertem Standard.
- Die Priorisierung gilt für NPC-Daten, szenenspezifische NPC-Daten und Szenendaten.
**Referenzen:** `doc/adr/002-datenspeicherung-data-verzeichnis.md`, `engine/storage.py`

### Überschreiben von Prompt-Templates
**Typ:** Funktional  
**Beschreibung:** Das System muss Prompt-Templates über gleichnamige Dateien unter `.overrides/prompts/` vollständig überschreibbar machen.  
**Akzeptanzkriterien:**
- Jedes Prompt-Template unter `prompts/` kann durch eine gleichnamige Datei unter `.overrides/prompts/` vollständig ersetzt werden.
- Ohne lokale Überschreibung bleibt das versionierte Template unter `prompts/` wirksam.
- Dies gilt auch für ein separates Prompt-Template mit gemeinsamen Bild-Style-Regeln, das von `Build`, `Refresh` und `Scene-Merge` verwendet wird.
**Referenzen:** `engine/storage.py`, `engine/config.py`, `doc/requirements/sg-007-dreistufige-bildgenerierung.md`

### Lokale Persistenz außerhalb von Git
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss das Verzeichnis `.overrides/` als lokale, nicht versionierte Anpassungsschicht außerhalb von Git vorsehen.  
**Akzeptanzkriterien:**
- Lokale Anpassungen können persistiert werden, ohne versionierte Projektdateien unter `npcs/` oder `scenes/` zu verändern.
- Das Verzeichnis `.overrides/` gehört nicht zur versionierten Ausgangsbasis des Projekts.
- Lokale Anpassungen in `.overrides/` sollen die Git-Historie des Projekts nicht verändern.
**Referenzen:** `doc/adr/002-datenspeicherung-data-verzeichnis.md`, `engine/config.py`
