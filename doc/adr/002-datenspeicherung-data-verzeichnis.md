---
state: implemented
---

# ADR-002: Laufzeitdaten unter `.data/` speichern

## Status
implemented

## Kontext
- Das Projekt trennt versionierte Initialdaten im Repository von Daten, die zur Laufzeit entstehen oder sich ändern.
- Ohne diese Trennung würden Laufzeitdaten Projektdateien überschreiben, das Debugging erschweren und die Git-Historie verschmutzen.

## Entscheidung
- Alle zur Laufzeit erzeugten oder veränderten Daten werden ausschließlich unter `.data/` gespeichert; Schreiboperationen in die versionierten Projektverzeichnisse finden nicht statt.

## Begründung
- Versionierte Initialdaten bleiben als unveränderte Ausgangsbasis und Fallback erhalten.
- Laufzeitdaten ändern sich dynamisch und sollen nicht in Git versioniert werden.
- Eine klare Trennung macht den aktuellen Laufzeitstand unabhängig von den Ausgangsdaten nachvollziehbar.

## Alternativen
### Alternative 1
- Laufzeitdaten direkt in `npcs/` und `scenes/` speichern.
- Verworfen, weil dadurch versionierte Ausgangsdaten überschrieben würden.

### Alternative 2
- Laufzeitdaten in mehreren getrennten Verzeichnissen je Datentyp speichern.
- Verworfen, weil Zurücksetzen, Verwaltung und Debugging dadurch unnötig komplexer würden.

### Alternative 3
- Laufzeitdaten vollständig in einer Datenbank speichern.
- Verworfen, weil das Projekt eine dateibasierte Ablage unter `.data/` vorsieht.

## Konsequenzen
- positiv: Projektdateien bleiben in einem sauberen, reproduzierbaren Zustand.
- negativ: Das System muss Initialdaten und Laufzeitdaten aus unterschiedlichen Speicherorten berücksichtigen.
- offen: Keine

## Annahmen
- `npcs/` und `scenes/` bleiben die versionierte Ausgangsbasis.
- Laufzeitdaten liegen weiterhin unter Pfaden wie `.data/npcs/<npc_id>/<scene_id>/state.md`, `.data/npcs/<npc_id>/<scene_id>/stm.jsonl`, `.data/npcs/<npc_id>/<scene_id>/img.png`, `.data/npcs/<npc_id>/<scene_id>/img_backup/img-<ts>.png` und `.data/npcs/<npc_id>/<scene_id>/scene.md`.
- Die Chroma Vector-Datenbank für ETM liegt pro Spielinstanz unter `.data/npcs/<npc_id>/<scene_id>/etm.chroma/` und unterliegt demselben `.data/`-Prinzip.

## Offene Fragen
- Keine

## Referenzen
- `engine/config.py`
