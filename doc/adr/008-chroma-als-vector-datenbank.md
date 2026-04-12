---
state: draft
---

# ADR-008: Chroma als lokal eingebettete Vector-Datenbank für ETM

## Status
draft

## Kontext
- SG-015 führt Episodic Term Memory (ETM) ein, das ältere STM-Gesprächsabschnitte als kompakte Episoden vektorisiert.
- Der Chat-Flow lädt semantisch passende Episoden pro `npc_id` + `scene_id` in den Prompt.
- Statischer Beziehungskontext wird separat über `relationship.md` in den initialen State eingebracht und nicht aus Chroma-Treffern fortgeschrieben.
- Bildgenerierung lädt ETM nicht direkt, sondern nutzt davon abgeleitete State- oder Scene-Informationen.
- Dafür wird eine lokale Vector-Datenbank benötigt, die ohne separaten Server betrieben werden kann und pro `npc_id` + `scene_id` klar isoliert ist.

## Entscheidung
- Die lokal eingebettete Vector-Datenbank ist Chroma.
- Jede Spielinstanz erhält eine eigene Chroma-Collection unter `.data/npcs/<npc_id>/<scene_id>/etm.chroma/`.
- Chroma wird für semantisches Retrieval von ETM-Episoden innerhalb derselben Spielinstanz verwendet.
- ETM-Retrieval wird im Dialog sowie in State- und Scene-Updates verwendet, nicht direkt in der Bildgenerierung.

## Begründung
- Chroma ist in Python nativ einbettbar und benötigt keinen separaten Server.
- Die dateibasierte Ablage je Spielinstanz passt direkt zum bestehenden `.data/`-Prinzip aus ADR-002.
- Der Scope per Pfad über `npc_id` und `scene_id` macht Isolation und Löschung beim Reset trivial.
- Der Chat-Flow kann dadurch kontextsensitive ETM-Episoden vor der Antwortgenerierung zusätzlich in den Prompt laden.
- Chroma bietet Metadaten-Filter und Similarity-Search, ohne manuelle Vektorarithmetik.
- Für die aktuelle Datenmenge von weniger als 100 Einträgen pro Spielinstanz ist die Performanz ausreichend.

## Alternativen
### Alternative 1
- Qdrant local mode verwenden.
- Verworfen, weil Qdrant mehr Setup erfordert und für die aktuelle Datenmenge überdimensioniert ist.

### Alternative 2
- `sqlite-vec` verwenden.
- Verworfen, weil dafür eine manuelle SQL-Integration nötig wäre und keine Python-native Abstraktionsschicht vorliegt.

### Alternative 3
- JSONL mit manueller Cosine-Similarity verwenden.
- Verworfen, weil das bei wachsender Datenmenge ineffizient und wartungsaufwendig wird.

## Konsequenzen
- positiv: Kein separater Server, keine Deployment-Änderung, trivialer Reset per Verzeichnis löschen.
- positiv: Der Chat-Flow erhält kontextsensitive ETM-Erinnerungen, ohne ein separates Langzeitgedächtnis-Artefakt als Sammelbecken für alte Gespräche zu verwenden.
- negativ: Neue Python-Abhängigkeit `chromadb`, aktuell kein Support für serverbasierte Skalierung.
- negativ: Jeder tatsächlich ausgeführte ETM-Retrieval-Kontext verursacht höchstens einen zusätzlichen Embedding-Request.
- offen: Bei sehr langen Spielsitzungen mit mehr als 1000 Einträgen oder sehr häufigen Dialoganfragen könnte die Performance evaluiert werden.

## Annahmen
- Chroma wird im embedded-Modus über `PersistentClient` betrieben.
- Pro Spielinstanz wird genau eine Chroma-Collection verwendet.
- ETM-Episoden werden als zusammenhängende Gesprächszusammenfassungen gespeichert, nicht als einzelne rohe Chat-Nachrichten.

## Offene Fragen
- Keine

## Referenzen
- `doc/requirements/sg-015-episodic-term-memory.md`
- `doc/adr/002-datenspeicherung-data-verzeichnis.md`
- `engine/stores/etm_vector_store.py`
- `engine/services/npc_turn_service.py`
