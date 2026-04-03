---
state: implemented
---

# SG-005: NPC-Bilder

## Kontext
Das System stellt Bilder für NPCs bereit.  
Der fachliche Fokus liegt auf visueller Darstellung von Charakteren.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Verfügbarkeit von NPC-Bildern
**Typ:** Funktional  
**Beschreibung:** Das System muss jedem NPC ein zugeordnetes Bild bereitstellen können.  
**Akzeptanzkriterien:**
- Für einen NPC kann ein Bild angezeigt werden.
- Bildzuordnungen bleiben pro NPC eindeutig.

**Referenzen:** Keine

### Laufzeit-Überlagerung von NPC-Bildern
**Typ:** Funktional  
**Beschreibung:** Das System muss für einen NPC-Szenen-Kontext ein Laufzeitbild unter `.data/npcs/<npc_id>/<scene_id>/img.png` nutzen können. Wenn ein solches Laufzeitbild vorhanden ist, muss es gegenüber den versionierten Standardbildern bevorzugt werden. Wenn kein solches Laufzeitbild vorhanden ist, muss das bestehende Fallback-Verhalten auf versionierte Bilddateien erhalten bleiben.  
**Akzeptanzkriterien:**
- Für einen NPC-Szenen-Kontext kann ein Laufzeitbild unter `.data/npcs/<npc_id>/<scene_id>/img.png` verwendet werden.
- Ist dort ein Laufzeitbild vorhanden, wird dieses anstelle der versionierten Standardbilder verwendet.
- Ist dort kein Laufzeitbild vorhanden, werden weiterhin die versionierten Standardbilddateien verwendet.

**Referenzen:** doc/adr/002-datenspeicherung-data-verzeichnis.md

### Konsistente Darstellung
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss die visuelle Darstellung eines NPCs konsistent halten.  
**Akzeptanzkriterien:**
- Ein NPC wird nicht ohne fachlichen Anlass mit stark wechselnder visueller Identität dargestellt.
- Die Bilddarstellung bleibt über Interaktionen hinweg wiedererkennbar.

**Referenzen:** Keine

### Kontextgerechte Nutzung
**Typ:** Randbedingung  
**Beschreibung:** Das System muss NPC-Bilder nur im Rahmen der vorgesehenen Spieloberfläche nutzen.  
**Akzeptanzkriterien:**
- Bilder werden in Bezug auf den jeweiligen NPC-Kontext angezeigt.
- Kontextfremde Bildzuordnungen treten nicht auf.

**Referenzen:** Keine
