# AGENTS.md – Social Game

## Architekturüberblick

Ein KI-gestütztes soziales Interaktionssystem mit persistenten NPC-Zuständen, Kurzzeitgedächtnis, ETM und LLM-gesteuerter Bildgenerierung.

**Hauptkomponenten:**
- `engine/web/app.py` – FastAPI-Backend + Lifespan-Start des Job-Schedulers
- `engine/tools/scheduler.py` – `Scheduler` mit vier fachlichen Jobs (`EtmJob`, `StateJob`, `SceneJob`, `ImageJob`)
- `engine/storage.py` – zentraler Zugriffspunkt für Session-/NPC-/Scene-/Prompt-Pfade und Laufzeitdaten
- `engine/llm/client.py` – LLM-Funktionen: `embed_texts`, `stream_prompt`, `run_prompt_small`, `refresh_img`, `merge_character_scene_img`
- `engine/cli.py` – Typer-CLI als Einstiegspunkt `sg`

## Datenpfade

**Statische Quelldaten (versioniert):**
- `npcs/<npc_id>/` → `description.md`, `state.md`, `system_prompt.md`, `character.yaml`, `img.png`
- `scenes/<scene_id>/scene.md` + `npcs/<npc_id>/scenes/<scene_id>/scene.md` (werden beim Laden zusammengeführt)
- `prompts/*.md` – alle LLM-Prompt-Templates mit `{{PLACEHOLDER}}`-Syntax

**Lokale Overrides (`.overrides/`, nicht versioniert):**
- `.overrides/npcs/<npc_id>/` und `.overrides/scenes/<scene_id>/` – überschreiben gleichnamige Initialdateien vollständig
- `.overrides/npcs/<npc_id>/scenes/<scene_id>/` – überschreibt NPC-szenenspezifische Assets (z. B. `scene.md`, `img.png`)
- `.overrides/prompts/*.md` – überschreibt Prompt-Templates vollständig

**Laufzeitdaten (`.data/`, nicht versioniert):**
- `.data/session.yaml` – aktiver NPC/Szene-Kontext mit Keys `npc_id` und `scene_id`
- `.data/npcs/<npc_id>/<scene_id>/` – überschreibt Initialzustand und hält Laufzeitgedächtnis (state.md, scene.md, stm.jsonl, etm_lightrag/, img.png)
- `.data/npcs/<npc_id>/<scene_id>/orchestrator/` – orchestrator-spezifische Laufzeitartefakte (z. B. gespeicherte Bildprompts)

**Priorität beim Laden:** Laufzeitdatei → `.overrides`-Datei → szenenspezifisches NPC-Asset → statisches Default.

## Developer-Workflows

```bash
# Setup
git config core.hooksPath .githooks
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

# Starten
sg web                                         # http://127.0.0.1:8000

# Browser-MCP/Edge-DevTools verbinden
microsoft-edge \
  --remote-debugging-port=9222 \
  --auto-open-devtools-for-tabs \
  --user-data-dir=.data/edge \
  http://localhost:8000
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

**Prompt-Templates** – Platzhalter per `.replace("{{KEY}}", value)`, kein Template-Engine:
```text
Path("prompts/image_build_prompt.md").read_text(encoding="utf-8").replace("{{NPC_DESCRIPTION}}", "<npc description>")
```

**Konfiguration** – alle Werte über `engine/config.py` (pydantic-settings), `.env` mit `SG_MODEL_API_KEY`, `SG_MODEL_BASE_URL`, `SG_MODEL_LLM_BIG`, `SG_MODEL_LLM_SMALL`, `SG_MODEL_IMAGE`, `SG_MODEL_EMBEDDING` (allgemein: `SG_`-Prefix für alle Config-Werte). Kein Direktzugriff auf `os.environ`.

**Fehlerbehandlung** – Provider-Fehler werden in `RuntimeError` mit lesbarer Meldung gewrappt; user-sichtbare Details werden über `user_visible_provider_error_detail(...)` normalisiert. Keine stillen Catches.

**Web-Frontend** – Vanilla-JS Web Components in `engine/web/static/js/`. Komponentenkommunikation ausschließlich via `CustomEvent`, kein direkter DOM-Zugriff auf Kind-Komponenten.

**Requirements-Dokumentation** – Anforderungen primär fachlich, nicht technisch formulieren:
- Technische Implementierungsdetails nur aufnehmen, wenn sie fachlich zwingend sind oder ohne sie die Anforderung nicht eindeutig/prüfbar wäre.
- Wenn technische Details unvermeidbar sind, diese bevorzugt als `Randbedingung` oder als separaten weiterführenden Hinweis dokumentieren, nicht als Kern der funktionalen Anforderung.
- Akzeptanzkriterien stets beobachtbares Verhalten beschreiben; interne Flags, Jobnamen, Klassen oder Endpunkte nur in begründeten Ausnahmefällen nennen.

## OpenCode-Agenten

Projekt-Agenten sind in `.opencode/agents/` definiert. `AGENTS.md` enthält nur globale Projektanweisungen; agentenspezifische Aktivierung, Regeln, Modelle und Berechtigungen stehen ausschließlich in den jeweiligen Agent-Dateien.

Verfügbare Agenten:
- `commit` – lokale Git-Commits erstellen
- `release` – lokalen Release-/Squash-Workflow ausführen
- `test` – Tests ausführen und Fehler korrigieren
- `review-code` – Code gegen Projektguidelines prüfen
- `requirements` – Anforderungen erstellen/überarbeiten
- `refactoring` – gezielte Refactorings ausführen
- `adr` – Architecture Decision Records erstellen

## Externe Abhängigkeiten

- **OpenAI** – Provider für Chat/Bilder/Embeddings über OpenAI-API
- **APScheduler** – Background-Scheduler für den periodischen `execute_pending_jobs()`-Loop (10s Intervall)
- **FastAPI + uvicorn** – Web-Backend
- **pydantic-settings** – Konfiguration
- **rapidfuzz** – Prompt-Ähnlichkeitsprüfung im `ImageService`
- **Pillow** – Bildkomprimierung vor LLM-Upload (PNG → JPEG)
- **LiteLLM (optional)** – kann für eigene Embedding-Modelle oder weitere OpenAI-kompatible Modellanbieter genutzt werden
