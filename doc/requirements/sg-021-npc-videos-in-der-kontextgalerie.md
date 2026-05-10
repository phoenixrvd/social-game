---
state: defined
---

# SG-021: NPC-Videos in der Kontextgalerie

## Kontext

NPCs können zusätzlich zum Bild ein Video besitzen.  
Für Olga liegt mit `npcs/olga/video.mp4` ein Beispiel für ein NPC-Video vor.
NPC-Videos dürfen keine Audiospur enthalten, weil mobile Clients sonst die übrige Audiowiedergabe pausieren können,
sobald eine NPC-Animation abgespielt wird.

## Annahmen

- Keine

## Offene Fragen

- Keine

## Anforderungen

### Wiedergabe vorhandener NPC-Videos in der Kontextgalerie

**Typ:** Funktional  
**Beschreibung:** Das System muss beim Anklicken des Medienbereichs in der Kontextgalerie für den aktiven NPC ein
vorhandenes NPC-Video anstelle des Bildes wiedergeben.  
**Akzeptanzkriterien:**

- Existiert für den aktiven NPC ein Video, kann der Medienbereich in der Kontextgalerie angeklickt werden.
- Nach dem Anklicken wird das vorhandene NPC-Video wiedergegeben.
- Während der Wiedergabe wird an dieser Stelle nicht stattdessen das Bild angezeigt.

**Referenzen:** `npcs/olga/video.mp4`, `engine/web/static/js/sg-context-gallery.js`,
`doc/requirements/sg-011-web-gui.md`

### Entfernen von Audiospuren aus NPC-Videos

**Typ:** Funktional  
**Beschreibung:** Das System muss ein Utility bereitstellen, mit dem Audiospuren aus allen vorhandenen NPC-Videos
entfernt werden können.  
**Akzeptanzkriterien:**

- Nach der Ausführung des Utilitys enthalten die vorhandenen NPC-Videos keine Audiospur mehr.
- Die Videospur bleibt erhalten und kann weiterhin in der Kontextgalerie wiedergegeben werden.
- Das Utility berücksichtigt NPC-Videos aus den Standarddaten und aus lokalen Overrides.

**Referenzen:** `npcs/*/video.mp4`, `.overrides/npcs/*/video.mp4`, `engine/cli.py`
