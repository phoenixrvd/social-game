---
state: implemented
---

# ADR-004: Modellstrategie

## Status
implemented

## Kontext
- Das Projekt benötigt KI-Modelle für Aufgaben mit unterschiedlichen Anforderungen an Qualität, Latenz und Kosten.
- Dialoge, Hilfsaufgaben der strukturierten Textverarbeitung, Embedding-basierte Retrieval-Schritte und Bildgenerierung werden getrennt über `.env`-konfigurierbare Settings gesteuert.

## Entscheidung
- Das Projekt verwendet getrennt konfigurierbare Modelle: `MODEL_LLM_BIG` für NPC-Dialoge, `MODEL_LLM_SMALL` für Hilfsaufgaben der strukturierten Textverarbeitung, `MODEL_LLM_IMG_BASE` für Bildgenerierung und `MODEL_EMBEDDING` (Standard: `text-embedding-3-small`) für die Vektorisierung von ETM-Episoden sowie für Retrieval-Queries im Chat-Flow.

## Begründung
- Dialoge brauchen mehr Kontexttreue und Konsistenz als Hilfsaufgaben.
- Hilfsaufgaben profitieren von geringerer Latenz und niedrigeren Kosten.
- Bildgenerierung ist eine eigene Aufgabe mit eigenen Anforderungen an Prompt-Verarbeitung und Ergebnisqualität.
- Ein gemeinsames Embedding-Modell hält die semantische Repräsentation zwischen ETM-Speicherung und Chat-Retrieval kompatibel.
- Die Konfiguration über `.env` erlaubt Modellwechsel ohne Code-Änderung.

## Alternativen
### Alternative 1
- Ein einziges Textmodell für alle Textaufgaben verwenden.
- Verworfen, weil Dialoge und Hilfsaufgaben unterschiedliche Anforderungen an Qualität, Latenz und Kosten haben.

### Alternative 2
- Modellnamen fest im Code hinterlegen.
- Verworfen, weil Modelle ohne Code-Änderung austauschbar bleiben sollen.

### Alternative 3
- Ein einziges Modell für Text- und Bildgenerierung verwenden.
- Verworfen, weil Bildgenerierung im Projekt als eigene Modellkonfiguration behandelt wird.

## Konsequenzen
- positiv: Modellwechsel sind über `.env` möglich, ohne den Code anzupassen.
- positiv: ETM-Speicherung und Chat-Flow nutzen denselben Embedding-Raum für konsistentes Retrieval.
- negativ: Mehrere Modellkonfigurationen erhöhen den Abstimmungs- und Testaufwand.
- negativ: Embedding-Modellwechsel wirken sich sowohl auf gespeicherte ETM-Episoden als auch auf ETM-Retrieval-Queries aus.
- offen: Keine

## Annahmen
- `MODEL_LLM_BIG`, `MODEL_LLM_SMALL`, `MODEL_LLM_IMG_BASE` und `MODEL_EMBEDDING` bleiben als Settings konfigurierbar.
- Dialoge und Hilfsaufgaben dürfen getrennte Textmodelle verwenden.
- `MODEL_EMBEDDING` wird für ETM-Similarity-Retrieval in fachlich passenden Kontexten verwendet.

## Offene Fragen
- Keine

## Referenzen
- `engine/config.py`
- `engine/llm_client.py`
- `engine/services/npc_turn_service.py`
