---
state: draft
---

# ADR-008: LightRAG als ETM-Store

## Status
draft

## Kontext
- SG-015 führt Episodic Term Memory (ETM) ein, das ältere STM-Gesprächsabschnitte als kompakte Episoden vektorisiert.
- Der Chat-Flow lädt semantisch passende Episoden pro `npc_id` + `scene_id` in den Prompt.
- Statischer Beziehungskontext ist Bestandteil von `state.md`, wird über den State geladen und nicht aus ETM-Treffern fortgeschrieben.
- Bildgenerierung lädt ETM nicht direkt, sondern nutzt davon abgeleitete State- oder Scene-Informationen.
- Dafür wird ein ETM-Store benötigt, der pro `npc_id` + `scene_id` klar isoliert ist und in die bestehende Storage-Architektur passt.
- ADR-011 beschreibt die übergreifende Memory-Entscheidung; dieses ADR konkretisiert den ETM-Store.

## Entscheidung
- Der ETM-Store nutzt LightRAG.
- ETM-Episoden werden mit Text und Embedding pro Spielinstanz in LightRAG verwaltet.
- Semantisches Retrieval erfolgt ueber LightRAG.
- ETM-Retrieval wird im Dialog sowie in State- und Scene-Updates verwendet, nicht direkt in der Bildgenerierung.

## Begründung
- LightRAG vereinheitlicht ETM-Indexierung und ETM-Retrieval in einem konsistenten Mechanismus.
- Die Ablage je Spielinstanz passt direkt zum bestehenden `.data/`-Prinzip aus ADR-002.
- Der Scope per Pfad über `npc_id` und `scene_id` macht Isolation und Löschung beim Reset trivial.
- Der Chat-Flow kann dadurch kontextsensitive ETM-Episoden vor der Antwortgenerierung zusätzlich in den Prompt laden.
- Die bestehende Modelllandschaft einschliesslich Embeddings kann unveraendert weiterverwendet werden.

## Alternativen
### Alternative 1
- ETM in einem eigenen, separaten Store ohne LightRAG fuehren.
- Verworfen, weil ETM-Indexierung und ETM-Retrieval dann ueber unterschiedliche Mechanismen laufen.

### Alternative 2
- SQLite-basierten ETM-Store mit eigener Distanzberechnung beibehalten.
- Verworfen, weil ETM-Retrieval damit weiterhin als eigener Spezialpfad gepflegt werden muss.

### Alternative 3
- LightRAG mit gleichzeitiger Umstellung der Modelllandschaft einfuehren.
- Verworfen, weil die gleichzeitige Aenderung von Architektur und Modellen das Einfuehrungsrisiko erhoeht.

## Konsequenzen
- positiv: ETM-Indexierung und ETM-Retrieval laufen ueber einen einheitlichen Mechanismus.
- positiv: Die bestehende Modell- und Embedding-Konfiguration bleibt stabil.
- positiv: ETM bleibt pro `npc_id` + `scene_id` isoliert nutzbar.
- negativ: Retrieval-Qualitaet von LightRAG wird kritischer Erfolgsfaktor fuer ETM-Qualitaet.
- negativ: Die konsistente Pflege der LightRAG-Artefakte erfordert klare Betriebsregeln.
- offen: Schwellenwerte fuer die erforderliche Retrieval-Qualitaet im Betrieb sind festzulegen.

## Annahmen
- Pro Spielinstanz wird ein isolierter LightRAG-Kontext verwendet.
- ETM-Episoden werden als zusammenhängende Gesprächszusammenfassungen gespeichert, nicht als einzelne rohe Chat-Nachrichten.

## Offene Fragen
- Keine

## Referenzen
- `doc/requirements/sg-015-episodic-term-memory.md`
- `doc/adr/002-datenspeicherung-data-verzeichnis.md`
- `doc/adr/011-memory-mit-lightrag.md`
- `engine/services/etm_service.py`
- `engine/services/npc_turn_service.py`
