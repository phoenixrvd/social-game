---
state: draft
---

# ADR-011: Memory mit LightRAG

## Status
draft

## Kontext
- ETM, Nutzer-Profil-Kontext und Faktenextraktion sind fachlich eng gekoppelt und sollen auf einer gemeinsamen Memory-Basis laufen.
- Die bestehende Nutzer-Profil-Eingabe bleibt manuell gepflegt und statisch.
- Das Projekt nutzt bereits konfigurierte Modelle fuer LLM und Embeddings.
- Es soll kein gleichzeitiger Modellwechsel erfolgen.

## Entscheidung
- Das Memory-System nutzt LightRAG als gemeinsamen Retrieval-Mechanismus.
- LightRAG wird fuer ETM-Retrieval, Nutzer-Profil-Kontextnutzung und Faktenextraktion eingesetzt.
- Die bestehende manuelle Nutzer-Profil-Eingabe bleibt als statische Quelle erhalten.
- Die aktuell konfigurierten Modelle einschliesslich Embedding-Modell bleiben unveraendert.

## Begründung
- Eine gemeinsame RAG-Basis reduziert fachliche Inkonsistenzen zwischen ETM, Profilkontext und Faktenableitung.
- Die unveraenderte Modelllandschaft reduziert Einfuehrungsrisiken und erleichtert Vergleichbarkeit im Betrieb.
- Die statische, manuelle Profilpflege bleibt fachlich kontrollierbar und nachvollziehbar.

## Alternativen
### Alternative 1
- Bestehenden ETM-Store und bestehendes Fakten-/Profilverhalten unveraendert lassen.
- Verworfen, weil ETM, Profilkontext und Faktenextraktion dann weiterhin getrennte Mechanismen nutzen.

### Alternative 2
- LightRAG nur fuer ETM nutzen, Profilkontext und Faktenextraktion separat belassen.
- Verworfen, weil die fachliche Vereinheitlichung damit ausbleibt.

### Alternative 3
- LightRAG einfuehren und gleichzeitig LLM- und Embedding-Modelle wechseln.
- Verworfen, weil die gleichzeitige Aenderung von Architektur und Modellen das Risiko in der Einfuehrung erhoeht.

## Konsequenzen
- positiv: ETM, Profilkontext und Faktenextraktion laufen auf einem gemeinsamen Retrieval-Mechanismus.
- positiv: Modell- und Embedding-Konfiguration bleibt stabil.
- positiv: Nutzer-Profil bleibt manuell steuerbar und wird nicht automatisch ueberschrieben.
- negativ: Retrieval-Qualitaet von LightRAG wird kritischer Erfolgsfaktor fuer Memory-Qualitaet.
- negativ: Die konsistente Pflege der LightRAG-Memory-Artefakte erfordert klare Betriebsregeln.
- offen: Konkrete Cutover-Kriterien und Rollback-Trigger sind noch festzulegen.

## Annahmen
- Die bestehende manuelle Profilpflege im System bleibt funktional erhalten.

## Offene Fragen
- Welche messbaren Schwellenwerte definieren die erforderliche Retrieval-Qualitaet im Betrieb?

## Referenzen
- `doc/requirements/sg-015-episodic-term-memory.md`
- `doc/requirements/sg-019-user-profile.md`
- `doc/adr/004-modellstrategie.md`
