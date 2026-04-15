---
state: implemented
---

# SG-017: Grok als konfigurierbarer Provider für Text, Bild und lokale Embeddings

## Kontext
Das System unterstützt OpenAI und Grok als auswählbare Provider für große Textanfragen, kleine Textanfragen, Bildanfragen und Embeddings. Die fachlichen Funktionen dieser Bereiche sind in `doc/requirements/sg-001-dialogbasierte-interaktionen.md`, `doc/requirements/sg-005-npc-bilder.md` und `doc/requirements/sg-015-episodic-term-memory.md` beschrieben; SG-017 regelt nur die Providerauswahl und die Grok-spezifischen Randbedingungen. Im Embedding-Bereich bedeutet `EMBEDDING=grok` aktuell einen lokalen Embedding-Pfad mit FastEmbed und nicht einen entfernten Grok-Embedding-API-Aufruf.

Nicht-normativer Hinweis: Bei `EMBEDDING=grok` wird aktuell mangels einer echten xAI-Embedding-Alternative lokal ein kleines FastEmbed-Modell verwendet; dessen Ergebnisqualität liegt derzeit unter den OpenAI-Embedding-Modellen.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Providerauswahl je LLM-Funktionsbereich
**Typ:** Funktional  
**Beschreibung:** Das System muss die Providerauswahl für große Textanfragen, kleine Textanfragen, Bildanfragen und Embeddings jeweils getrennt konfigurierbar machen.  
**Akzeptanzkriterien:**
- Für `LLM_BIG`, `LLM_SMALL`, `IMAGE` und `EMBEDDING` ist jeweils `openai` oder `grok` auswählbar.
- Gemischte Providerkombinationen über diese vier Bereiche sind zulässig.
- Der für einen Bereich konfigurierte Provider bestimmt den in diesem Bereich verwendeten Client.
**Referenzen:** `engine/config.py`, `engine/llm/client_adapter.py`, `tests/test_config.py`

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
**Referenzen:** `engine/config.py`, `engine/llm/client.py`, `engine/llm/client_grok.py`, `tests/test_config.py`

### Grok-Textanfragen ohne serverseitige Speicherung
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss Grok-basierte Textanfragen ohne serverseitige Speicherung absenden.  
**Akzeptanzkriterien:**
- Grok-basierte große Textanfragen werden mit `store=False` gesendet.
- Grok-basierte kleine Textanfragen werden mit `store=False` gesendet.
- Für große Textanfragen bleibt Streaming verfügbar.
**Referenzen:** `engine/llm/client_grok.py`, `doc/requirements/sg-001-dialogbasierte-interaktionen.md`

### Grok als auswählbarer Bild-Provider
**Typ:** Funktional  
**Beschreibung:** Das System muss Grok für Bildanfragen als auswählbaren Provider unterstützen.  
**Akzeptanzkriterien:**
- Bei `IMAGE=grok` werden Bildanfragen an den Grok-Bildclient geleitet.
- Eine Grok-Bildanfrage kann genau ein Referenzbild verarbeiten.
- Eine Grok-Bildanfrage kann mehrere Referenzbilder gemeinsam verarbeiten.
- Das Ergebnis einer Grok-Bildanfrage kann als Binärdaten, Base64-Daten oder URL übernommen werden.
**Referenzen:** `engine/llm/client.py`, `engine/llm/client_adapter.py`, `engine/llm/client_grok.py`, `tests/test_config.py`, `tests/test_llm_client.py`, `doc/requirements/sg-005-npc-bilder.md`

### Grok-Embeddings ohne Grok-API-Zugang
**Typ:** Randbedingung  
**Beschreibung:** Das System muss im Grok-Embedding-Pfad Embeddings ohne Grok-API-Zugang bereitstellen.  
**Akzeptanzkriterien:**
- `EMBEDDING=grok` ist zulässig, auch wenn `GROK_API_KEY` leer ist.
- Der Grok-Embedding-Pfad erzeugt Embeddings lokal.
- Der Grok-Embedding-Pfad verwendet dafür das lokale Modell `sentence-transformers/all-MiniLM-L6-v2`.
- Der lokale Modellcache liegt unter `storage.etm_fastembed_cache`.
- Fehlt das lokale Modell noch, darf es beim ersten tatsächlichen Embedding-Aufruf in diesen Cache geladen werden.
- Leere Eingabelisten liefern keine Embeddings.
**Referenzen:** `engine/config.py`, `engine/llm/client_adapter.py`, `engine/llm/client_grok.py`, `engine/storage.py`, `tests/test_config.py`, `tests/test_llm_client.py`, `tests/test_storage.py`, `doc/requirements/sg-015-episodic-term-memory.md`
