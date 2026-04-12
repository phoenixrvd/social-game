# AGENTS.md – Social Game

## Architekturüberblick

Ein KI-gestütztes soziales Interaktionssystem mit persistenten NPC-Zuständen, Kurzzeitgedächtnis, ETM und LLM-gesteuerter Bildgenerierung.

**Hauptkomponenten:**
- `engine/web/app.py` – FastAPI-Backend + Background-Scheduler-Start
- `engine/updater/` – Vier spezialisierte Hintergrund-Updater (etm, scene, state, image), alle erben von `AbstractUpdater`
- `engine/stores/npc_store.py` – Einziger Zugriffspunkt für NPC-Kontext; überblendet Initialzustand mit Laufzeitdaten
- `engine/llm_client.py` – LLM-Funktionen: `hello_llm`, `embed_texts`, `stream_prompt`, `run_prompt`, `refresh_img`, `merge_character_scene_img`
- `engine/cli.py` – Typer-CLI als Einstiegspunkt `sg`

## Datenpfade

**Statische Quelldaten (versioniert):**
- `npcs/<npc_id>/` → `description.md`, `state.md`, `relationship.md`, `system_prompt.md`, `character.yaml`, `img.png`
- `scenes/<scene_id>/scene.md` + `npcs/<npc_id>/scenes/<scene_id>/scene.md` (werden beim Laden zusammengeführt)
- `prompts/*.md` – alle LLM-Prompt-Templates mit `{{PLACEHOLDER}}`-Syntax

**Laufzeitdaten (`.data/`, nicht versioniert):**
- `.data/session.yaml` – aktiver NPC/Szene-Kontext
- `.data/npcs/<npc_id>/<scene_id>/` – überschreibt Initialzustand und hält Laufzeitgedächtnis (state.md, scene.md, stm.jsonl, etm.chroma, img.png)
- `.data/npcs/<npc_id>/<scene_id>/orchestrator/` – Flag-Dateien und gespeicherte Prompts für Updater

**Priorität beim Laden:** Laufzeitdatei → szenenspezifisches NPC-Asset → statisches Default.

## Developer-Workflows

```bash
# Setup
git config core.hooksPath .githooks
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

# Starten
sg web                                         # http://127.0.0.1:8000
sg session-set --npc mira --scene cafe         # aktiven Kontext wechseln
sg update image                                # Updater einmalig manuell auslösen
sg image-merge-scene                           # Charakter-Szenenbild neu zusammenführen
sg image-revert                                # letztes Backup wiederherstellen
sg hallo-llm                                   # LLM-Verbindung prüfen

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

**Updater-Pattern** – jeder Updater implementiert `schedule()` und `get_update_interval()`:
- `_should_run_for_npc(npc)` prüft ob neue STM-Nachrichten seit letztem Check vorhanden sind
- ImageUpdater zusätzlich flag-basiert: `emit_update()` schreibt `.flag`, `schedule()` konsumiert es
- `force=True` deaktiviert Skip-Logik (Prompt-Ähnlichkeitsprüfung)

**Prompt-Templates** – Platzhalter per `.replace("{{KEY}}", value)`, kein Template-Engine:
```python
load_text(config.PROJECT_ROOT / "prompts" / "image_build_prompt.md").replace("{{NPC_DESCRIPTION}}", npc.description)
```

**Konfiguration** – alle Werte über `engine/config.py` (pydantic-settings), `.env`-Datei für `OPENAI_API_KEY`. Kein Direktzugriff auf `os.environ`.

**Fehlerbehandlung** – OpenAI-Fehler werden in `RuntimeError` mit lesbarer Meldung gewrappt; nur wenn fachliche Reaktion nötig. Keine stillen Catches.

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

- **OpenAI** – Chat (`gpt-*`), Bildgenerierung (`gpt-image-*`) via `client.images.edit`
- **APScheduler** – Background-Scheduler für Updater-Loop
- **FastAPI + uvicorn** – Web-Backend
- **pydantic-settings** – Konfiguration
- **rapidfuzz** – Prompt-Ähnlichkeitsprüfung im ImageUpdater
- **Pillow** – Bildkomprimierung vor LLM-Upload (PNG → JPEG)
