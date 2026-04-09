---
state: implemented
---

# SG-014: Initiale Bildgenerierung aus NPC- und Szenenkontext

## Kontext
Das System soll für den aktiven NPC-Szenen-Kontext eine initiale Bilderzeugung aus aktivem NPC und zusammengeführter Szenenbeschreibung bereitstellen. Die NPC-szenenspezifische Ergänzung (Kurzbeschreibung) ist Bestandteil dieser zusammengeführten Szenenbeschreibung.  
SG-014 beschreibt Auslösung, Eingabebasis und Speicherung des Initialbildes; allgemeine Anforderungen an NPC-Bilder werden referenziert.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Manuelle Auslösung der initialen Bilderzeugung
**Typ:** Funktional  
**Beschreibung:** Das System muss die initiale Bilderzeugung für den aktiven NPC-Szenen-Kontext manuell auslösbar bereitstellen.  
**Akzeptanzkriterien:**
- Die initiale Bilderzeugung kann für den aktiven NPC-Szenen-Kontext manuell gestartet werden.
- Das CLI kann diese manuelle Auslösung bereitstellen.

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
**Beschreibung:** Das System muss für die initiale Bilderzeugung die zusammengeführte Szenenbeschreibung des aktiven NPC-Szenen-Kontexts verwenden. Diese besteht aus der Basisszene der aktiven Szene und der NPC-szenenspezifischen Ergänzung.  
**Akzeptanzkriterien:**
- Die für die initiale Bilderzeugung verwendete Szenenbeschreibung entspricht der zusammengeführten Szenenbeschreibung des aktiven NPC-Szenen-Kontexts (`npc.scene.description`).
- Die verwendete Szenenbeschreibung enthält die Basisszene der aktiven Szene.
- Die verwendete Szenenbeschreibung enthält die NPC-szenenspezifische Ergänzung des aktiven NPC für die aktive Szene.

**Referenzen:** `doc/requirements/sg-006-dynamischer-scene-state.md`, `prompts/image_scene.md`

### Einbezug der NPC-szenenspezifischen Ergänzung
**Typ:** Funktional  
**Beschreibung:** Das System muss die NPC-szenenspezifische Ergänzung der aktiven Szene für die initiale Bilderzeugung verwenden. Diese Ergänzung ist Teil von `npc.scene.description` und kein separater Texteingang.  
**Akzeptanzkriterien:**
- Die initiale Bilderzeugung verwendet die NPC-szenenspezifische Ergänzung des aktiven NPC für die aktive Szene.
- Die NPC-szenenspezifische Ergänzung wird über die zusammengeführte Szenenbeschreibung (`npc.scene.description`) eingebracht.
- Für diesen Bestandteil wird kein separater Texteingang außerhalb von `npc.scene.description` verwendet.

**Referenzen:** `doc/requirements/sg-006-dynamischer-scene-state.md`, `prompts/image_scene.md`

### Backup vor Ersetzung des aktiven Laufzeitbildes
**Typ:** Funktional  
**Beschreibung:** Das System muss ein bestehendes aktives Laufzeitbild des betroffenen NPC-Szenen-Kontexts vor seiner Ersetzung sichern.  
**Akzeptanzkriterien:**
- Wenn bereits ein aktives Laufzeitbild vorhanden ist, existiert vor dem Speichern des neuen Initialbildes ein Backup dieses Bildes.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`, `doc/adr/002-datenspeicherung-data-verzeichnis.md`

### Speicherung als aktives Laufzeitbild
**Typ:** Funktional  
**Beschreibung:** Das System muss das erzeugte Initialbild als aktives Laufzeitbild des betroffenen NPC-Szenen-Kontexts speichern.  
**Akzeptanzkriterien:**
- Nach erfolgreicher initialer Bilderzeugung ist das neue Bild als aktives Laufzeitbild des betroffenen NPC-Szenen-Kontexts gespeichert.

**Referenzen:** `doc/requirements/sg-005-npc-bilder.md`, `doc/adr/002-datenspeicherung-data-verzeichnis.md`

### Persistierung eines Initialwerts für den Image-Updater
**Typ:** Funktional  
**Beschreibung:** Das System muss nach erfolgreicher initialer Bildgenerierung für den betroffenen NPC-Szenen-Kontext einen Initialwert für den Image-Updater persistieren.  
**Akzeptanzkriterien:**
- Nach erfolgreicher initialer Bildgenerierung steht für den betroffenen NPC-Szenen-Kontext ein persistierter Initialwert für den Image-Updater zur Verfügung.
- Der persistierte Initialwert entspricht dem für die anschließende Bildfortschreibung maßgeblichen Bildprompt und nicht dem Prompt der initialen Bildgenerierung.
- Wird der Image-Updater unmittelbar danach für denselben NPC-Szenen-Kontext ohne relevante Kontextänderung ausgeführt, entsteht kein neues Bild allein deshalb, weil ein initialer Promptwert fehlt.

**Referenzen:** `doc/requirements/sg-007-dreistufige-bildgenerierung.md`, `doc/requirements/sg-008-llm-based-update-orchesrator-for-scene-ltm-image.md`, `doc/adr/002-datenspeicherung-data-verzeichnis.md`, `prompts/image_build_prompt.md`
