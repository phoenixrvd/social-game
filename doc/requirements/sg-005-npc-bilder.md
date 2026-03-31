---
state: implemented
---

# SG-005: NPC-Bilder

NPCs sollen ein Charakterbild besitzen, das auf einem statischen Referenzbild basiert und bei Bedarf als aktuelles Datenbild aktualisiert werden kann.

## Technische Details

### Bildquellen und Lade-Priorität

Beim Laden des aktuellen NPC-Bildes gilt folgende Priorität (erste vorhandene Datei gewinnt):

1. `.data/npcs/<npc_id>/<scene_id>/img.png` – generiertes Laufzeitbild für die aktive Szene.
2. `npcs/<npc_id>/scenes/<scene_id>/img.png` – statisches szenenspezifisches Bild des NPC.
3. `npcs/<npc_id>/img.png` – statisches Referenzbild des NPC (szenenunabhängig).

Das statische Referenzbild (`npcs/<npc_id>/img.png`) bleibt die fachliche Ausgangsbasis für neue Bildgenerierungen.

### Bildgenerierung

- Der Bild-Workflow besteht aus zwei fachlichen Stufen:
  1. Ein Rohprompt wird aus NPC-Daten, aktuellem State, Szenenbeschreibung, relevantem Dialogkontext und Long-Term-Memory aufgebaut.
  2. Dieser Rohprompt wird mit `prompts/image_build_prompt.md` zu einem kompakten Bildprompt optimiert und anschließend zusammen mit dem Referenzbild für die Bildgenerierung verwendet.
- Der optimierte Bildprompt wird unter `.data/image/character_prompt.md` gespeichert.
- Das Bildmodell erhält für die eigentliche Generierung:
  1. das aktuelle Referenzbild,
  2. den optimierten Bildprompt.
- Der Rohprompt wird nicht direkt an das Bildmodell geschickt.

### Ausgabeformat und Modelle

- Das Bild wird als `png` erzeugt mit `moderation=low`, `orientation=portrait`, `size=1024x1536`.
- Das verwendete Bildmodell kommt aus `.env` über `MODEL_LLM_IMG_BASE` (Default: `gpt-image-1.5`).
- Für die Optimierung des Rohprompts wird ein Text-LLM verwendet.

### Persistenz und Backups

- Persistenzort für neue Bilder: `.data/npcs/<npc_id>/img.png`.
- Vor dem Persistieren wird ein vorhandenes Datenbild nach `.data/npcs/<npc_id>/img_backup/img-<date>-<time>.png` verschoben.
- Der optimierte Bildprompt wird bei jedem persistierten Bild-Update überschrieben.

### Auslösung und Bedienverhalten

- Die reguläre Bildaktualisierung wird durch den `ImageUpdater` im Orchestrator-/Web-Betrieb angestoßen, sobald relevante Änderungen in Szene oder State erkannt wurden.
- Die Web-GUI zeigt das aktuell gültige Bild an und aktualisiert es asynchron im Hintergrund.
- Wird in der Web-GUI das Laufzeitverzeichnis `.data/npcs/<npc_id>` des aktiven NPC geloescht (Reset), faellt die Bildauswahl auf das statische Referenzbild `npcs/<npc_id>/img.png` zurueck, bis wieder ein neues Datenbild erzeugt wurde.

### Revert (`sg image-revert`)

- Der Befehl `sg image-revert` setzt das generierte Datenbild des aktuell aktiven Session-NPC auf den letzten Backup-Stand zurueck.
- Ablauf:
  1. Falls `.data/npcs/<npc_id>/img.png` vorhanden ist, wird es gelöscht.
  2. Falls ein Backup (`img-<date>-<time>.png`) unter `.data/npcs/<npc_id>/img_backup/` vorhanden ist, wird das jüngste davon als neues `img.png` wiederhergestellt.
  3. Sind weder Datenbild noch Backup vorhanden, gibt die CLI eine entsprechende Meldung aus.
- Die CLI gibt aus, was getan wurde (gelöscht / Backup wiederhergestellt).

## Akzeptanzkriterien

- Jeder NPC kann ein statisches Referenzbild, optionale szenenspezifische Bilder und ein generiertes Laufzeitbild besitzen.
- Das aktive Bild folgt der Priorität: Laufzeitbild (Szene) → statisches Szenenbild → statisches Referenzbild.
- Der Bild-Workflow verwendet einen zweistufigen Ablauf aus Prompt-Optimierung und Bildgenerierung.
- Der optimierte Bildprompt wird unter `.data/image/character_prompt.md` gespeichert.
- Der `ImageUpdater` erzeugt auf Basis des Referenzbildes und des optimierten Bildprompts ein neues Datenbild.
- Vor dem Überschreiben eines vorhandenen Datenbildes wird ein Backup angelegt.
- Der Befehl `sg image-revert` löscht ein vorhandenes Datenbild und stellt das jüngste Backup wieder her, falls eines vorhanden ist.
- Nach einem NPC-Reset in der Web-GUI wird ein zuvor vorhandenes Laufzeitbild unter `.data/npcs/<npc_id>/<scene_id>/img.png` nicht mehr verwendet; die GUI zeigt bis zur nächsten Generierung das szenenspezifische Statik-Bild oder das Referenzbild.
