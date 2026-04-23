---
state: implemented
---

# ADR-004: Modellstrategie

## Status
implemented

## Kontext
- Das Projekt benötigt KI-Modelle für Aufgaben mit unterschiedlichen Anforderungen an Qualität, Latenz und Kosten.
- Dialoge, Hilfsaufgaben der strukturierten Textverarbeitung und Bildgenerierung werden über `.env`-konfigurierbare Provider- und Modell-Settings gesteuert.
- Embeddings für ETM werden lokal im ETM-Service erzeugt und nutzen kein externes Embedding-Modell.

## Entscheidung
- Das Projekt verwendet getrennt konfigurierbare Modelle: `MODEL_LLM_BIG` für NPC-Dialoge, `MODEL_LLM_SMALL` für Hilfsaufgaben der strukturierten Textverarbeitung und `MODEL_LLM_IMG_BASE` für Bildgenerierung.
- Embeddings werden zentral über den `EtmService` erzeugt (lokales FastEmbed-Modell `sentence-transformers/all-MiniLM-L6-v2`), damit ETM-Speicherung und ETM-Retrieval denselben Embedding-Raum nutzen.

## Begründung
- Dialoge brauchen mehr Kontexttreue und Konsistenz als Hilfsaufgaben.
- Hilfsaufgaben profitieren von geringerer Latenz und niedrigeren Kosten.
- Bildgenerierung ist eine eigene Aufgabe mit eigenen Anforderungen an Prompt-Verarbeitung und Ergebnisqualität.
- Der zentrale ETM-Service verhindert Provider-Streuung und stellt einheitliche Embeddings im gesamten System sicher.
- Die Konfiguration über `.env` erlaubt Modellwechsel für LLM/Bild ohne Code-Änderung.

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
- positiv: ETM-Speicherung und Chat-Flow nutzen denselben lokalen Embedding-Raum für konsistentes Retrieval.
- positiv: Es gibt keinen externen Embedding-Provider und damit keine zusätzliche Provider-Komplexität für Embeddings.
- negativ: Mehrere Modellkonfigurationen erhöhen den Abstimmungs- und Testaufwand.
- negativ: Ein Wechsel des lokalen Embedding-Modells wirkt sich sowohl auf gespeicherte ETM-Episoden als auch auf ETM-Retrieval-Queries aus.
- offen: Keine

## Annahmen
- `MODEL_LLM_BIG`, `MODEL_LLM_SMALL` und `MODEL_LLM_IMG_BASE` bleiben als Settings konfigurierbar.
- Dialoge und Hilfsaufgaben dürfen getrennte Textmodelle verwenden.
- Der EtmService wird für alle ETM-Embeddings im System verwendet.

## Offene Fragen
- Keine

## Referenzen
- `engine/config.py`
- `engine/services/etm_service.py`
- `engine/services/npc_turn_service.py`
