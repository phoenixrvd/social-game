# Laufzeitprozess ETM-Erstellung

## Zweck

Dieses Dokument beschreibt den Laufzeitprozess zur Erstellung von Episodic Term Memory (ETM) im aktiven NPC-Szenen-Kontext.
ETM speichert ältere STM-Nachrichten als abrufbare Episoden aus Sicht des NPC.

## Beteiligte Komponenten

- `engine/tools/scheduler.py`: stößt periodisch `run_pending_tools()` an
- `engine/tools/etm_tool.py`: führt ETM-Update fachlich aus
- `engine/tools/orchestrator.py`: stellt Tool-Registry und gecachte Tool-Instanzen bereit
- `engine/services/etm_update_service.py`: erzeugt ETM-Episoden, Embeddings und räumt verarbeitete STM-Nachrichten auf
- `engine/services/etm_retrieval_service.py`: lädt relevante ETM-Episoden für Chat, State und Scene
- `engine/stores/etm_vector_store.py`: kapselt Chroma unter `.data/npcs/<npc_id>/<scene_id>/etm.chroma/`
- `engine/stores/npc_store.py`: lädt NPC-, Szenen-, STM- und LTM-Kontext
- `engine/llm/client.py`: ruft Textmodell und Embedding-Modell auf

## Überblick

Die ETM-Erstellung läuft batch-orientiert:

1. Nach einer final erfolgreich gestreamten Chat-Nachricht ruft der Web-Flow `Scheduler.schedule_all()` auf.
2. Dadurch wird `etm` als pending Tool markiert.
3. Der `Scheduler` ruft periodisch `Scheduler.run_pending_tools()` auf.
4. Der `Scheduler` prüft pending Tools und führt `EtmTool.execute()` rate-limitiert aus.
5. Es werden alle STM-Nachrichten außer den letzten `config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP` ausgewählt.
6. Wenn die Anzahl dieser älteren Nachrichten `<= config.UPDATER_ETM_BATCH_SIZE_THRESHOLD` ist, endet der Lauf.
7. `prompts/etm_update.md` verdichtet den Batch zu einer ETM-Episode aus Sicht des NPC.
8. Die Episode wird über `MODEL_EMBEDDING` vektorisiert.
9. Die Episode wird unter `.data/npcs/<npc_id>/<scene_id>/etm.chroma/` gespeichert.
10. Die verarbeiteten STM-Nachrichten werden aus `stm.jsonl` entfernt.

LLM-Tool-/Function-Calling wird dafür nicht verwendet. Hintergrund: In diesem Modus liefert das Modell typischerweise keine normale Antwort. Ein Twice-Call-Pattern würde für dieselbe fachliche Wirkung unnötige Kosten und zusätzliche Komplexität verursachen.

ETM schreibt keine `relationship.md`. Der statische Beziehungskontext bleibt getrennt und wird nur als Initialkontext für den State verwendet.

## Retrieval-Kontexte

ETM wird geladen für:

- NPC-Antworten im Chat
- State-Updates, wenn das `state`-Tool ausgeführt wird
- Scene-Updates, wenn das `scene`-Tool ausgeführt wird

ETM wird nicht direkt geladen für:

- Bildgenerierung
- Web-GUI-Initialkontext

Die Web-GUI zeigt sichtbaren Beziehungs- oder Langzeitkontext aus LTM.
Bildgenerierung nutzt ETM nur indirekt, wenn relevante ETM-Inhalte vorher in State oder Scene eingeflossen sind.

## Embedding-Grenzen

ETM-Retrieval erzeugt höchstens einen Embedding-Request pro tatsächlich ausgeführtem Retrieval-Kontext.
Ohne vorhandenen ETM-Speicher, bei leerem Query-Text oder in Kontexten ohne ETM-Nutzung wird kein Embedding-Request erzeugt.

## Konfiguration

- `UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP`: `20`
- `UPDATER_ETM_BATCH_SIZE_THRESHOLD`: `7`
- `UPDATER_ETM_CHECK_INTERVAL_SECONDS`: `350`
- `ETM_RETRIEVAL_TOP_K`: `4`
- `ETM_RETRIEVAL_MAX_DISTANCE`: `0.35`

## Artefakte

- `.data/npcs/<npc_id>/<scene_id>/stm.jsonl`
- `.data/npcs/<npc_id>/<scene_id>/etm.chroma/`
- `prompts/etm_update.md`
