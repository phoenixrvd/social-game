---
state: implemented
---

# SG-014: Initiale Bildgenerierung aus NPC- und Szenenkontext

## Kontext
Das System stellt für den aktiven NPC in der aktiven Szene ein erstes Bild auf Basis der Charaktergrundlage und der vollständigen Szenenbeschreibung bereit. Die NPC-szenenspezifische Ergänzung ist Bestandteil dieser Beschreibung.  
SG-014 beschreibt Auslösung, fachliche Eingaben, Sicherung, Ablage und die Grundlage für die spätere Bildfortschreibung; allgemeine Anforderungen an NPC-Bilder werden referenziert.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Manuelle Auslösung der initialen Bilderzeugung
**Typ:** Funktional  
**Beschreibung:** Das System muss die erstmalige Bilderzeugung für den aktiven NPC in der aktiven Szene manuell auslösbar bereitstellen.  
**Akzeptanzkriterien:**
- Die erstmalige Bilderzeugung kann für den aktiven NPC in der aktiven Szene bewusst gestartet werden.
- Für diese Auslösung steht ein vorgesehener manueller Bedienweg zur Verfügung.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`

### Nutzung des aktiven NPC-Szenen-Kontexts
**Typ:** Funktional  
**Beschreibung:** Das System muss die initiale Bilderzeugung auf den aktiven NPC-Szenen-Kontext beziehen.  
**Akzeptanzkriterien:**
- Wird die initiale Bilderzeugung gestartet, betrifft sie den aktiven NPC und die aktive Szene.
- Solange ein aktiver NPC-Szenen-Kontext vorliegt, ist dafür keine separate Kontextauswahl erforderlich.

**Referenzen:** Keine

### Einbezug des aktiven NPC als Charaktergrundlage
**Typ:** Funktional  
**Beschreibung:** Das System muss den aktiven NPC als Charaktergrundlage der initialen Bilderzeugung verwenden.  
**Akzeptanzkriterien:**
- Die initiale Bilderzeugung bezieht sich auf den aktiven NPC als darzustellenden Charakter.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`

### Einbezug der zusammengeführten Szenenbeschreibung
**Typ:** Funktional  
**Beschreibung:** Das System muss für die erstmalige Bilderzeugung die vollständige Szenenbeschreibung des aktiven NPC in der aktiven Szene verwenden. Diese umfasst die allgemeine Szene und die NPC-spezifische Ergänzung.  
**Akzeptanzkriterien:**
- Die verwendete Szenenbeschreibung entspricht der vollständigen Beschreibung des aktiven NPC in der aktiven Szene.
- Die verwendete Szenenbeschreibung enthält die allgemeine Beschreibung der aktiven Szene.
- Die verwendete Szenenbeschreibung enthält die NPC-spezifische Ergänzung für die aktive Szene.

**Referenzen:** `doc/requirements/sg-006-dynamischer-scene-state.md`, `prompts/image_scene.md`

### Einbezug der NPC-szenenspezifischen Ergänzung
**Typ:** Funktional  
**Beschreibung:** Das System muss die NPC-spezifische Ergänzung der aktiven Szene für die erstmalige Bilderzeugung berücksichtigen.  
**Akzeptanzkriterien:**
- Die erstmalige Bilderzeugung berücksichtigt die NPC-spezifische Ergänzung für die aktive Szene.
- Diese Ergänzung wird als Teil der vollständigen Szenenbeschreibung verwendet.
- Sie wird nicht als eigenständige, davon getrennte Eingabe behandelt.

**Referenzen:** `doc/requirements/sg-006-dynamischer-scene-state.md`, `prompts/image_scene.md`

### Backup vor Ersetzung des aktiven Laufzeitbildes
**Typ:** Funktional  
**Beschreibung:** Das System muss ein bereits verwendetes Bild des betroffenen NPC in der aktiven Szene vor seiner Ersetzung sichern.  
**Akzeptanzkriterien:**
- Wenn bereits ein verwendetes Bild vorhanden ist, existiert vor dem Speichern des neuen ersten Bildes eine Sicherung dieses Bildes.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`, `doc/adr/002-datenspeicherung-data-verzeichnis.md`

### Speicherung als aktives Laufzeitbild
**Typ:** Funktional  
**Beschreibung:** Das System muss das erzeugte erste Bild als aktuell verwendetes Bild des betroffenen NPC in der aktiven Szene ablegen.  
**Akzeptanzkriterien:**
- Nach erfolgreicher erstmaliger Bilderzeugung ist das neue Bild als aktuell verwendetes Bild des betroffenen NPC in der aktiven Szene verfügbar.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`, `doc/adr/002-datenspeicherung-data-verzeichnis.md`

### Persistierung eines Ausgangswerts für die Bildfortschreibung
**Typ:** Funktional  
**Beschreibung:** Das System muss nach erfolgreicher erstmaliger Bilderzeugung für den betroffenen NPC in der aktiven Szene einen Ausgangswert für spätere Bildfortschreibungen festhalten.  
**Akzeptanzkriterien:**
- Nach erfolgreicher erstmaliger Bilderzeugung ist für den betroffenen NPC in der aktiven Szene ein Ausgangswert für spätere Bildfortschreibungen vorhanden.
- Dieser Ausgangswert entspricht der fachlich maßgeblichen Bildbeschreibung für die weitere Fortschreibung und nicht nur der Beschreibung, die zur Erzeugung des ersten Bildes verwendet wurde.
- Wird die Bildfortschreibung unmittelbar danach ohne relevante Änderung des Kontexts erneut ausgelöst, entsteht kein neues Bild allein deshalb, weil ein Ausgangswert fehlt.

**Referenzen:** `doc/requirements/sg-007-dreistufige-bildgenerierung.md`, `doc/requirements/sg-008-llm-based-update-orchesrator-for-scene-ltm-image.md`, `doc/adr/002-datenspeicherung-data-verzeichnis.md`, `prompts/image_build_prompt.md`
