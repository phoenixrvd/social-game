---
state: implemented
---

# ADR-004: Modellstrategie

## Status
implemented

## Kontext
- Das Projekt benötigt KI-Modelle für Aufgaben mit unterschiedlichen Anforderungen an Qualität, Latenz und Kosten.
- Dialoge, Hilfsaufgaben der strukturierten Textverarbeitung und Bildgenerierung werden über `.env`-konfigurierbare Provider- und Modell-Settings gesteuert.
- Embeddings fuer ETM werden zentral ueber einen OpenAI-kompatiblen Endpoint erzeugt.

## Entscheidung
- Das Projekt verwendet getrennt konfigurierbare Modelle: `MODEL_LLM_BIG` fuer NPC-Dialoge, `MODEL_LLM_SMALL` fuer Hilfsaufgaben der strukturierten Textverarbeitung, `MODEL_IMAGE` fuer Bildgenerierung und `MODEL_EMBEDDING` fuer ETM-Embeddings.
- Embeddings werden zentral ueber den `EtmService` erzeugt (OpenAI-kompatible API), damit ETM-Speicherung und ETM-Retrieval denselben Embedding-Raum nutzen.

## Begründung
- Dialoge brauchen mehr Kontexttreue und Konsistenz als Hilfsaufgaben.
- Hilfsaufgaben profitieren von geringerer Latenz und niedrigeren Kosten.
- Bildgenerierung ist eine eigene Aufgabe mit eigenen Anforderungen an Prompt-Verarbeitung und Ergebnisqualität.
- Der zentrale ETM-Service stellt einheitliche Embeddings im gesamten System sicher.
- Die Konfiguration ueber `.env` erlaubt Modellwechsel fuer LLM/Bild/Embeddings ohne Code-Aenderung.
- Fuer eigene Embedding-Modelle kann ein OpenAI-kompatibler Gateway wie LiteLLM genutzt werden.

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
- positiv: ETM-Speicherung und Chat-Flow nutzen denselben Embedding-Raum fuer konsistentes Retrieval.
- positiv: Eigene Embedding-Modelle lassen sich ueber OpenAI-kompatible Gateways (z. B. LiteLLM) anbinden.
- negativ: Mehrere Modellkonfigurationen erhöhen den Abstimmungs- und Testaufwand.
- negativ: Ein Wechsel des Embedding-Modells wirkt sich sowohl auf gespeicherte ETM-Episoden als auch auf ETM-Retrieval-Queries aus.
- offen: Keine

## Annahmen
- `MODEL_LLM_BIG`, `MODEL_LLM_SMALL`, `MODEL_IMAGE` und `MODEL_EMBEDDING` bleiben als Settings konfigurierbar.
- Dialoge und Hilfsaufgaben dürfen getrennte Textmodelle verwenden.
- Der EtmService wird für alle ETM-Embeddings im System verwendet.

## Offene Fragen
- Keine

## Referenzen
- ADR-009: Storage-Architektur und Zugriffsschicht
- `engine/config.py`
- `engine/services/etm_service.py`
- `engine/services/npc_turn_service.py`
