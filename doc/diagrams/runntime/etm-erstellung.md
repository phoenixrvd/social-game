# Laufzeitprozess ETM-Erstellung

## Zweck

Dieses Dokument beschreibt den Laufzeitprozess zur Erstellung von Episodic Term Memory (ETM) im aktiven NPC-Szenen-Kontext.
ETM speichert ältere STM-Nachrichten als abrufbare Episoden aus Sicht des NPC.

## Beteiligte Komponenten

- `engine/updater/etm_updater.py`: prüft STM-Batch-Größe und neue Nachrichten
- `engine/services/etm_update_service.py`: erzeugt ETM-Episoden, Embeddings und räumt verarbeitete STM-Nachrichten auf
- `engine/services/etm_retrieval_service.py`: lädt relevante ETM-Episoden für Chat, State und Scene
- `engine/stores/etm_vector_store.py`: kapselt Chroma unter `.data/npcs/<npc_id>/<scene_id>/etm.chroma/`
- `engine/stores/npc_store.py`: lädt NPC-, Szenen-, STM- und LTM-Kontext
- `engine/llm_client.py`: ruft Textmodell und Embedding-Modell auf

## Überblick

Die ETM-Erstellung läuft batch-orientiert:

1. `EtmUpdater.schedule()` lädt den aktiven NPC-Kontext.
2. Es werden alle STM-Nachrichten außer den letzten `config.UPDATER_ETM_SHORT_MEMORY_MESSAGES_TO_KEEP` ausgewählt.
3. Wenn die Anzahl dieser älteren Nachrichten `<= config.UPDATER_ETM_BATCH_SIZE_THRESHOLD` ist, endet der Lauf.
4. Wenn seit dem letzten ETM-Lauf keine neuen Nachrichten eingegangen sind, endet der Lauf.
5. `prompts/etm_episode.md` verdichtet den Batch zu einer ETM-Episode aus Sicht des NPC.
6. Die Episode wird über `MODEL_EMBEDDING` vektorisiert.
7. Die Episode wird unter `.data/npcs/<npc_id>/<scene_id>/etm.chroma/` gespeichert.
8. Die verarbeiteten STM-Nachrichten werden aus `stm.jsonl` entfernt.

ETM schreibt keine `relationship.md`. Der statische Beziehungskontext bleibt getrennt und wird nur als Initialkontext für den State verwendet.

## Retrieval-Kontexte

ETM wird geladen für:

- NPC-Antworten im Chat
- State-Updates, wenn der State-Updater aufgrund neuer STM-Nachrichten läuft
- Scene-Updates, wenn der Scene-Updater aufgrund neuer STM-Nachrichten läuft

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
- `.data/npcs/<npc_id>/<scene_id>/orchestrator/etm_updater_last_check.txt`
- `prompts/etm_episode.md`
