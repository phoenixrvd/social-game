# AGENTS.md – Social Game

## Architekturüberblick

Ein KI-gestütztes soziales Interaktionssystem mit persistenten NPC-Zuständen, Kurzzeitgedächtnis, ETM und LLM-gesteuerter Bildgenerierung.

**Hauptkomponenten:**
- `engine/web/app.py` – FastAPI-Backend + Lifespan-Start des Job-Schedulers
- `engine/tools/scheduler.py` – `Scheduler` mit vier fachlichen Jobs (`EtmJob`, `StateJob`, `SceneJob`, `ImageJob`)
- `engine/storage.py` – zentrale Pfadauflösung für Runtime-/Override-/Default-Daten und Prompt-Overrides
- `engine/stores/npc_store.py` – Einziger Zugriffspunkt für NPC-Kontext; überblendet Initialzustand mit Laufzeitdaten
- `engine/llm/client.py` – LLM-Funktionen: `embed_texts`, `stream_prompt`, `run_prompt_small`, `refresh_img`, `merge_character_scene_img`
- `engine/cli.py` – Typer-CLI als Einstiegspunkt `sg`

## Datenpfade

**Statische Quelldaten (versioniert):**
- `npcs/<npc_id>/` → `description.md`, `state.md`, `relationship.md`, `system_prompt.md`, `character.yaml`, `img.png`
- `scenes/<scene_id>/scene.md` + `npcs/<npc_id>/scenes/<scene_id>/scene.md` (werden beim Laden zusammengeführt)
- `prompts/*.md` – alle LLM-Prompt-Templates mit `{{PLACEHOLDER}}`-Syntax

**Lokale Overrides (`.overrides/`, nicht versioniert):**
- `.overrides/npcs/<npc_id>/` und `.overrides/scenes/<scene_id>/` – überschreiben gleichnamige Initialdateien vollständig
- `.overrides/npcs/<npc_id>/scenes/<scene_id>/` – überschreibt NPC-szenenspezifische Assets (z. B. `scene.md`, `img.png`)
- `.overrides/prompts/*.md` – überschreibt Prompt-Templates vollständig

**Laufzeitdaten (`.data/`, nicht versioniert):**
- `.data/session.yaml` – aktiver NPC/Szene-Kontext
- `.data/npcs/<npc_id>/<scene_id>/` – überschreibt Initialzustand und hält Laufzeitgedächtnis (state.md, scene.md, stm.jsonl, etm.chroma, img.png)
- `.data/npcs/<npc_id>/<scene_id>/orchestrator/` – orchestrator-spezifische Laufzeitartefakte (z. B. gespeicherte Bildprompts)
- `.data/fastembed_cache/` – lokaler Cache für Embeddings beim Grok-Embedding-Pfad

**Priorität beim Laden:** Laufzeitdatei → `.overrides`-Datei → szenenspezifisches NPC-Asset → statisches Default.

## Developer-Workflows

```bash
# Setup
git config core.hooksPath .githooks
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

# Starten
sg web                                         # http://127.0.0.1:8000
sg session-set --npc mira --scene cafe         # aktiven Kontext wechseln
sg image-merge-scene                           # Charakter-Szenenbild neu zusammenführen
sg image-revert                                # letztes Backup wiederherstellen

# Tests
pytest                                         # alle Tests
```

## Projektspezifische Muster

**Guidelines** – vor Codeänderungen die passenden Dateien unter `doc/guidelines/` beachten:
- `doc/guidelines/coding-rules.md` – verbindliche Coding-Regeln, insbesondere alle `[BLOCKER]`
- `doc/guidelines/error-handling.md` – Fehlerbehandlung
- `doc/guidelines/refactoring.md` – Refactoring-Vorgehen
- `doc/guidelines/principles.md` – allgemeine Entwicklungsprinzipien
- `doc/guidelines/web-components.md` – Web-Component-Regeln bei Frontend-Änderungen
- `doc/guidelines/git-workflow.md` – Git-/Commit-Vorgaben

Bei Konflikten gelten spezifischere Guidelines vor allgemeinen Mustern in dieser Datei.

**Agent-/Job-Pattern** – fachliche Updates laufen als Job-Ausführungen über den Scheduler:
- Jobs erben von `AbstractJob` und definieren `rate_limit_seconds` und `execute()`
- Nach einer final erfolgreich gestreamten Chat-Nachricht wird `Scheduler.enqueue_all()` aufgerufen
- Ohne neue final verarbeitete Chat-Nachricht werden keine fachlichen Jobs neu vorgemerkt
- Der `Scheduler` ruft periodisch `execute_pending_jobs()` auf (alle 10 Sekunden via APScheduler)
- Der Scheduler hält pending Jobs intern und führt sie synchron sowie rate-limitiert aus; Scheduler-Zyklen allein erzeugen keine neuen Job-Läufe
- LLM-Antworten und fachliche Updates sind bewusst getrennt; es gibt keine LLM-Tool-/Function-Calls mehr
- Hintergrund: Tool-/Function-Calling verhindert oft die normale Antwort. Ein Twice-Call-Pattern würde für dasselbe Ergebnis unnötige Kosten und Komplexität erzeugen
- `force=True` bei Bildupdates deaktiviert die Prompt-Skip-Logik

**Prompt-Templates** – Platzhalter per `.replace("{{KEY}}", value)`, kein Template-Engine:
```text
Path("prompts/image_build_prompt.md").read_text(encoding="utf-8").replace("{{NPC_DESCRIPTION}}", "<npc description>")
```

**Konfiguration** – alle Werte über `engine/config.py` (pydantic-settings), `.env` mit Provider-spezifischen Schlüsseln (`OPENAI_*`, `GROK_*`) und Provider-Schaltern pro Fähigkeit (`LLM_BIG`, `LLM_SMALL`, `IMAGE`, `EMBEDDING`). Kein Direktzugriff auf `os.environ`.

**Fehlerbehandlung** – Provider-Fehler (OpenAI/Grok) werden in `RuntimeError` mit lesbarer Meldung gewrappt; user-sichtbare Details werden über `user_visible_provider_error_detail(...)` normalisiert. Keine stillen Catches.

**Web-Frontend** – Vanilla-JS Web Components in `engine/web/static/js/`. Komponentenkommunikation ausschließlich via `CustomEvent`, kein direkter DOM-Zugriff auf Kind-Komponenten.

## Coding-Regeln (BLOCKER)

- Vollständige Regeln stehen in `doc/guidelines/coding-rules.md` und sind verbindlich.
- Methoden max. ~30 Zeilen, Verschachtelung max. 2–3 Ebenen
- Konstruktoren nutzen kein keyword-only `*`-Pattern
- Klassen instanziieren benötigte Stores und Services selbst; keine Store-/Service-Übergabe über Konstruktorparameter
- Keine Proxy-/Delegationsmethoden ohne eigene Logik
- Keine globalen Konstanten ohne echte Wiederverwendung (>2x im Modul)
- Unbenutzten Code sofort entfernen

## Git-Workflow

- Arbeit in `v1.x`-Branches, kein direkter Push auf `main`
- Squash-Merge auf `main` beim Release: `git merge --squash --ff v1.x`
- Commit-Format: `<type>: <beschreibung>` – Typen: `feature:`, `fix:`, `refactor:`, `add:`

## Externe Abhängigkeiten

- **OpenAI** – Provider für Chat/Bilder/Embeddings über OpenAI-API
- **xAI SDK (`xai-sdk`)** – Grok-Bildgenerierung via `Client.image.sample(...)`
- **APScheduler** – Background-Scheduler für den periodischen `execute_pending_jobs()`-Loop (10s Intervall)
- **FastAPI + uvicorn** – Web-Backend
- **pydantic-settings** – Konfiguration
- **chromadb** – persistenter ETM-Vector-Store (`engine/stores/etm_vector_store.py`)
- **fastembed** – lokaler Embedding-Pfad für Grok (`engine/llm/grok_provider_client.py`)
- **rapidfuzz** – Prompt-Ähnlichkeitsprüfung im `ImageService`
- **Pillow** – Bildkomprimierung vor LLM-Upload (PNG → JPEG)
