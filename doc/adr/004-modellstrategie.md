---
state: implemented
---

# ADR-004: Modellstrategie

## Status
implemented

## Kontext
- Das Projekt benötigt KI-Modelle für Aufgaben mit unterschiedlichen Anforderungen an Qualität, Latenz und Kosten.
- Dialoge, Hilfsaufgaben der strukturierten Textverarbeitung und Bildgenerierung werden getrennt über `.env`-konfigurierbare Settings gesteuert.

## Entscheidung
- Das Projekt verwendet getrennt konfigurierbare Modelle: `MODEL_LLM_BIG` für NPC-Dialoge und LTM-Zusammenfassung, `MODEL_LLM_SMALL` für Hilfsaufgaben der strukturierten Textverarbeitung und `MODEL_LLM_IMG_BASE` für Bildgenerierung.

## Begründung
- Dialoge brauchen mehr Kontexttreue und Konsistenz als Hilfsaufgaben.
- Hilfsaufgaben profitieren von geringerer Latenz und niedrigeren Kosten.
- Bildgenerierung ist eine eigene Aufgabe mit eigenen Anforderungen an Prompt-Verarbeitung und Ergebnisqualität.
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
- negativ: Mehrere Modellkonfigurationen erhöhen den Abstimmungs- und Testaufwand.
- offen: Keine

## Annahmen
- `MODEL_LLM_BIG`, `MODEL_LLM_SMALL` und `MODEL_LLM_IMG_BASE` bleiben als Settings konfigurierbar.
- Dialog und LTM-Zusammenfassung dürfen dasselbe große Modell verwenden.

## Offene Fragen
- Keine

## Referenzen
- `engine/config.py`
- `engine/llm_client.py`

