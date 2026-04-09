---
state: implemented
---

# SG-005: NPC-Bilder

## Kontext
Das System soll für den aktiven NPC-Szenen-Kontext NPC-Bilder bereitstellen und verwenden.  
SG-005 beschreibt Verfügbarkeit, Auswahl und Zuordnung von NPC-Bildern; die initiale Bilderzeugung aus aktivem NPC und zusammengeführter Szenenbeschreibung (`npc.scene.description`) mit NPC-szenenspezifischer Ergänzung statt separatem Texteingang ist in `doc/requirements/sg-014-initiale-bildgenerierung-aus-npc-und-szenenkontext.md` beschrieben.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Verfügbarkeit von NPC-Bildern
**Typ:** Funktional  
**Beschreibung:** Das System muss für den aktiven NPC-Szenen-Kontext ein NPC-Bild bereitstellen können.  
**Akzeptanzkriterien:**
- Für den aktiven NPC-Szenen-Kontext kann ein Bild angezeigt werden.
- Ein angezeigtes Bild ist genau einem NPC-Szenen-Kontext zugeordnet.

**Referenzen:** Keine

### Bevorzugung des aktiven Laufzeitbildes
**Typ:** Funktional  
**Beschreibung:** Das System muss für den aktiven NPC-Szenen-Kontext ein aktives Laufzeitbild gegenüber versionierten Standardbildern bevorzugen.  
**Akzeptanzkriterien:**
- Ist für den aktiven NPC-Szenen-Kontext ein aktives Laufzeitbild unter `.data/npcs/<npc_id>/<scene_id>/img.png` vorhanden, wird dieses verwendet.
- Ist dort kein aktives Laufzeitbild vorhanden, werden weiterhin die versionierten Standardbilder verwendet.

**Referenzen:** `doc/adr/002-datenspeicherung-data-verzeichnis.md`

### Initiale Bilderzeugung ohne bestehendes szenenspezifisches Bild
**Typ:** Funktional  
**Beschreibung:** Das System muss für die Aktualisierung des aktiven NPC-Bildes die initiale Bilderzeugung gemäß SG-014 verwenden, wenn im aktiven NPC-Szenen-Kontext weder ein aktives Laufzeitbild noch ein szenenspezifisches NPC-Bild vorliegt.  
**Akzeptanzkriterien:**
- Wird `/api/image/refresh-active` aufgerufen und es existiert weder ein aktives Laufzeitbild unter `.data/npcs/<npc_id>/<scene_id>/img.png` noch ein szenenspezifisches NPC-Bild unter `npcs/<npc_id>/scenes/<scene_id>/img.png`, wird die initiale Bilderzeugung gemäß SG-014 verwendet.
- In diesem Fall erfolgt keine reguläre Bildfortschreibung.

**Referenzen:** `doc/requirements/sg-014-initiale-bildgenerierung-aus-npc-und-szenenkontext.md`, `doc/adr/002-datenspeicherung-data-verzeichnis.md`

### Kontextgerechte Zuordnung von NPC-Bildern
**Typ:** Randbedingung  
**Beschreibung:** Das System muss NPC-Bilder dem jeweils passenden NPC-Szenen-Kontext zuordnen.  
**Akzeptanzkriterien:**
- Für den aktiven NPC-Szenen-Kontext wird kein Bild eines anderen NPC-Szenen-Kontexts verwendet.
- Ein Bildwechsel in einem NPC-Szenen-Kontext ändert nicht das Bild eines anderen NPC-Szenen-Kontexts.

**Referenzen:** Keine
