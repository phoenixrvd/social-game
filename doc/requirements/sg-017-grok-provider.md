---
state: implemented
---

# SG-017: Grok als konfigurierbarer Provider für Text und Bild

## Kontext
Das System unterstützt OpenAI und Grok als auswählbare Provider für große Textanfragen, kleine Textanfragen und Bildanfragen. Die fachlichen Funktionen dieser Bereiche sind in `doc/requirements/sg-001-dialogbasierte-interaktionen.md` und `doc/requirements/sg-005-npc-bilder.md` beschrieben; SG-017 regelt nur die Providerauswahl und die Grok-spezifischen Randbedingungen.

Embeddings sind davon getrennt und werden zentral über ein lokales Embedding-Service bereitgestellt (siehe `doc/requirements/sg-015-episodic-term-memory.md`).

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Providerauswahl je LLM-Funktionsbereich
**Typ:** Funktional  
**Beschreibung:** Das System muss die Providerauswahl für große Textanfragen, kleine Textanfragen und Bildanfragen jeweils getrennt konfigurierbar machen.  
**Akzeptanzkriterien:**
- Für `LLM_BIG`, `LLM_SMALL` und `IMAGE` ist jeweils `openai` oder `grok` auswählbar.
- Gemischte Providerkombinationen über diese drei Bereiche sind zulässig.
- Der für einen Bereich konfigurierte Provider bestimmt den in diesem Bereich verwendeten Client.
**Referenzen:** `engine/config.py`, `engine/llm/client.py`, `tests/test_config.py`

### Grok-spezifische Konfiguration für Text und Bild
**Typ:** Randbedingung  
**Beschreibung:** Das System muss Grok-basierte Text- und Bildanfragen über getrennte Grok-Konfigurationswerte unabhängig von OpenAI konfigurieren.  
**Akzeptanzkriterien:**
- Grok-basierte große Textanfragen verwenden `GROK_MODEL_LLM_BIG`.
- Grok-basierte kleine Textanfragen verwenden `GROK_MODEL_LLM_SMALL`.
- Grok-basierte Bildanfragen verwenden `GROK_MODEL_LLM_IMG_BASE`.
- Grok-basierte Textanfragen verwenden `GROK_API_KEY` und `GROK_BASE_URL`.
- Grok-basierte Bildanfragen verwenden `GROK_API_KEY`.
- OpenAI- und Grok-Konfigurationswerte sind getrennt vorhanden.
**Referenzen:** `engine/config.py`, `engine/llm/client.py`, `engine/llm/grok_provider_client.py`, `tests/test_config.py`

### Grok-Textanfragen ohne serverseitige Speicherung
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss Grok-basierte Textanfragen ohne serverseitige Speicherung absenden.  
**Akzeptanzkriterien:**
- Grok-basierte große Textanfragen werden mit `store=False` gesendet.
- Grok-basierte kleine Textanfragen werden mit `store=False` gesendet.
- Für große Textanfragen bleibt Streaming verfügbar.
**Referenzen:** `engine/llm/grok_provider_client.py`, `doc/requirements/sg-001-dialogbasierte-interaktionen.md`

### Grok als auswählbarer Bild-Provider
**Typ:** Funktional  
**Beschreibung:** Das System muss Grok für Bildanfragen als auswählbaren Provider unterstützen.  
**Akzeptanzkriterien:**
- Bei `IMAGE=grok` werden Bildanfragen an den Grok-Bildclient geleitet.
- Eine Grok-Bildanfrage kann genau ein Referenzbild verarbeiten.
- Eine Grok-Bildanfrage kann mehrere Referenzbilder gemeinsam verarbeiten.
- Das Ergebnis einer Grok-Bildanfrage kann als Binärdaten, Base64-Daten oder URL übernommen werden.
**Referenzen:** `engine/llm/client.py`, `engine/llm/grok_provider_client.py`, `tests/test_config.py`, `tests/test_llm_client.py`, `doc/requirements/sg-005-npc-bilder.md`
