---
state: implemented
---

# ADR-008: SQLite als lokal eingebetteter ETM-Store

## Status
draft

## Kontext
- SG-015 führt Episodic Term Memory (ETM) ein, das ältere STM-Gesprächsabschnitte als kompakte Episoden vektorisiert.
- Der Chat-Flow lädt semantisch passende Episoden pro `npc_id` + `scene_id` in den Prompt.
- Statischer Beziehungskontext wird separat über `relationship.md` in den initialen State eingebracht und nicht aus ETM-Treffern fortgeschrieben.
- Bildgenerierung lädt ETM nicht direkt, sondern nutzt davon abgeleitete State- oder Scene-Informationen.
- Dafür wird ein lokaler ETM-Store benötigt, der ohne separaten Server betrieben werden kann und pro `npc_id` + `scene_id` klar isoliert ist.

## Entscheidung
- Der ETM-Store ist eine lokale SQLite-Datei unter `.data/npcs/<npc_id>/<scene_id>/etm.sqlite`.
- ETM-Episoden werden mit Text und Embedding pro Spielinstanz in SQLite gespeichert.
- Semantisches Retrieval nutzt Cosine-Distanz, nativ in Python auf den gespeicherten Embeddings berechnet.
- ETM-Retrieval wird im Dialog sowie in State- und Scene-Updates verwendet, nicht direkt in der Bildgenerierung.

## Begründung
- Für den aktuellen Anwendungsfall mit knapp über 1000 Einträgen pro Spielinstanz ist eine native Cosine-Berechnung in Python ausreichend performant.
- Die dateibasierte Ablage je Spielinstanz passt direkt zum bestehenden `.data/`-Prinzip aus ADR-002.
- Der Scope per Pfad über `npc_id` und `scene_id` macht Isolation und Löschung beim Reset trivial.
- Der Chat-Flow kann dadurch kontextsensitive ETM-Episoden vor der Antwortgenerierung zusätzlich in den Prompt laden.
- Es ist nicht notwendig, dafür eine zusätzliche Vector-DB-Abhängigkeit wie Chroma mitzuführen.

## Alternativen
### Alternative 1
- Qdrant local mode verwenden.
- Verworfen, weil Qdrant mehr Setup erfordert und für die aktuelle Datenmenge überdimensioniert ist.

### Alternative 2
- Chroma als eingebettete Vector-Datenbank verwenden.
- Verworfen, weil der Anwendungsfall mit knapp über 1000 Einträgen die zusätzliche Abhängigkeit nicht rechtfertigt.

### Alternative 3
- JSONL mit manueller Cosine-Similarity verwenden.
- Verworfen, weil das bei wachsender Datenmenge ineffizient und wartungsaufwendig wird.

## Konsequenzen
- positiv: Kein separater Server, keine Deployment-Änderung, trivialer Reset per Verzeichnis löschen.
- positiv: Der Chat-Flow erhält kontextsensitive ETM-Erinnerungen, ohne ein separates Langzeitgedächtnis-Artefakt als Sammelbecken für alte Gespräche zu verwenden.
- positiv: Wegfall der Abhängigkeit `chromadb` und einfacher Runtime-Stack.
- negativ: Distanzberechnung und Ranking liegen vollständig in eigener Verantwortung.
- negativ: Jeder tatsächlich ausgeführte ETM-Retrieval-Kontext verursacht höchstens einen zusätzlichen Embedding-Request.
- offen: Bei deutlich mehr als 1000 Einträgen oder häufigeren Abfragen muss die Performance erneut evaluiert werden.

## Annahmen
- Pro Spielinstanz wird genau eine SQLite-Datei verwendet.
- ETM-Episoden werden als zusammenhängende Gesprächszusammenfassungen gespeichert, nicht als einzelne rohe Chat-Nachrichten.

## Offene Fragen
- Keine

## Referenzen
- `doc/requirements/sg-015-episodic-term-memory.md`
- `doc/adr/002-datenspeicherung-data-verzeichnis.md`
- `engine/services/etm_service.py`
- `engine/services/npc_turn_service.py`
