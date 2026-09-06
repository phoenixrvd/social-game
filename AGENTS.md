# AGENTS.md - Social Game

## Schnellstart (verifiziert)

- Python ist auf `3.14` ausgelegt (CI nutzt `actions/setup-python@v5` mit `python-version: '3.14'`).
- Setup: `git config core.hooksPath .githooks && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.dev.txt`.
- App starten: `./sg web` (ruft `engine.api.app.run` auf, Default `127.0.0.1:8000`).
- Tests (CI-Quelle): `pytest`.
- Gezielter Test: `pytest tests/test_web_app.py::test_index_serves_gui`.
- Frontend-Checks: `npm run typecheck` und `npm run build`.

## Reale Entry Points

- CLI: `sg` -> `engine/cli.py` (Typer-App).
- Backend: `engine/api/app.py` (FastAPI, Router + Security-Header + Lifespan).
- Chat-Stream: `POST /api/chat/stream` in `engine/api/chat.py`.
- LLM-Client: `engine/client.py` (Text, Embeddings, Bildgenerierung, Fehlernormalisierung).
- Storage-Fassade: `engine/storage/__init__.py` -> `engine/storage/facade.py`.

## Laufzeitfluss, der leicht übersehen wird

- Der Scheduler startet im FastAPI-Lifespan (`engine/api/app.py`) und läuft per APScheduler-Intervall alle `10s`.
- Fachliche Jobs (`etm`, `state`, `scene`, `image`) werden **nicht** zyklisch neu eingeplant; sie werden nach finaler Chat-Antwort per `get_scheduler().enqueue_all()` vorgemerkt (`engine/api/chat.py`).
- `Scheduler.execute_pending_jobs()` arbeitet pending Jobs synchron ab und respektiert Job-spezifische `rate_limit_seconds`.

## Datenpriorität und Dateipfade

- Aktiver Kontext: `.data/session.yaml` mit `npc_id` und `scene_id`.
- Runtime-Daten liegen unter `.data/npcs/<npc_id>/<scene_id>/` (z. B. `state.md`, `scene.md`, `stm.jsonl`, `etm_lightrag/`, `img.png`).
- Overrides liegen unter `.overrides/...` und sind nicht versioniert.
- Auflösung erfolgt über `engine/storage/paths.py`; Priorität ist runtime -> override -> default (mit Fallback auf Default-NPC/Default-Scene).
- Prompt-Dateien: `.overrides/prompts/*.md` übersteuern `prompts/*.md`.

## Frontend-Besonderheiten

- React-Quellcode liegt in `engine/web/react/`; Build-Ziel ist `engine/web/static/js` (siehe `vite.config.js`).
- Das Node-Tooling verwendet ausschließlich ES-Module (`"type": "module"`); Konfigurationen exportieren per `export default`.
- `engine/web/static/index.html` bindet `/js/theme-init.js` und `/js/app.js` direkt ein; nach React-Änderungen daher `npm run build` ausführen.
- Die React-UI nutzt eine verbindliche Container/View-Trennung für Features und Options-Panels: Container enthalten Datenzugriff, Commands, Router, Query, lokalen State und Props-Mapping; Views rendern nur Props und rufen Callback-Props auf.
- Feature- und Panel-Container sollen im Regelfall nur die zugehörige View direkt aufrufen. Reine Shared-UI-Komponenten brauchen keine Container/View-Trennung, solange sie keine fachliche Daten-, Router-, Query- oder Command-Logik enthalten.
- GUI-Texte sind Deutsch mit korrekten Umlauten (z. B. `zurück`, `löschen`, `größer`).
- Deutsche Texte immer mit korrekten Umlauten schreiben (kein `ae/oe/ue` als Ersatz).

## Sprache und Umlaute

- Alle deutschen Texte im Repository müssen korrekte Umlaute enthalten (`ä`, `ö`, `ü`, `Ä`, `Ö`, `Ü`, `ß`).
- Das gilt für Code-Kommentare, Docstrings, API-Beschreibungen, Fehlermeldungen, UI-Texte und Dokumentation.
- Umschreibungen wie `ae/oe/ue/ss` sind in deutschen Texten nicht erlaubt.
- Ausnahmen nur bei technischen Bezeichnern, die aus Kompatibilitätsgründen ASCII bleiben müssen (z. B. Dateinamen, Slugs, Legacy-Keys).

## Konventionen mit hoher Fehlerwahrscheinlichkeit

- Konfiguration ausschließlich über `engine/config.py` (`pydantic-settings`, Env-Prefix `SG_`); kein direkter `os.environ`-Zugriff in Fachcode.
- Prompt-Templates werden per String-Replacement mit `{{KEY}}` verarbeitet, nicht per Template-Engine.
- Provider-Fehler als `RuntimeError` mit nutzerlesbarer Meldung propagieren; in HTTP/API-Schicht werden Problem-Details geliefert (`application/problem+json`).
- Dependencies: direkte Pakete in `requirements.in` pflegen; `requirements.txt` nur via `pip-compile requirements.in` aktualisieren.

## Agenten und Zusatzkontext

- Repo-spezifische OpenCode-Agenten liegen in `.opencode/agents/`.
- MCP-Konfiguration liegt in `.opencode/opencode.json` (Edge DevTools via `npx chrome-devtools-mcp --browser-url=http://127.0.0.1:9222`).
