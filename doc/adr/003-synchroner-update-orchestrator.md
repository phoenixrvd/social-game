---
state: implemented
---

# ADR-003: Synchroner Job-Scheduler

## Status
implemented

## Kontext
- Das System aktualisiert ETM, State, Scene und Image auf Basis von STM, bestehendem Kontext und spezialisierten Prompt-Templates.
- LLM-Tool-/Function-Calling wurde verworfen, weil das Modell in diesem Modus typischerweise keine normale Antwort mehr liefert.
- Um sowohl eine normale Antwort als auch Tool-Ausführung zu erhalten, wäre ein Twice-Call-Pattern nötig.
- Dieses Twice-Call-Pattern hätte für dasselbe Ergebnis unnötige Kosten und zusätzliche Komplexität.
- Beim Start von `sg web` läuft ein Scheduler automatisch mit; Ziel sind deterministisches Verhalten, Debuggbarkeit und klar getrennte Verantwortlichkeiten zwischen Antworterzeugung und Hintergrund-Updates.

## Entscheidung
- Updates für ETM, State, Scene und Image werden zeitgesteuert über den `Scheduler` ausgeführt.
- LLM-Tool-/Function-Calling wird für diese Updates nicht verwendet.
- Nach einer final erfolgreich gestreamten Chat-Nachricht aktiviert der Scheduler alle fachlichen Jobs über `enqueue_all()`.
- Ohne neue final verarbeitete Chat-Nachricht werden keine fachlichen Jobs neu vorgemerkt.
- Der Scheduler führt die pending Jobs anschließend in `execute_pending_jobs()` rate-limitiert aus.
- Der Scheduler verwaltet Job-Instanzen direkt ohne Orchestrator-Zwischenschicht.

## Begründung
- Synchrones, zeitgesteuertes Ausführen erhöht Nachvollziehbarkeit und Determinismus.
- Antworterzeugung und fachliche Updates bleiben getrennt steuerbar.
- Das vermeidet das Twice-Call-Pattern und damit unnötige Zusatzkosten.
- Der automatische Start im Web-Lifecycle verhindert separate manuelle Startschritte.

## Alternativen
### Alternative 1
- Updates über LLM-Tool-/Function-Calling ausführen.
- Verworfen, weil das Modell dabei typischerweise keine normale Antwort mehr liefert.

### Alternative 2
- Twice-Call-Pattern einsetzen: ein LLM-Aufruf für die Antwort, ein weiterer für Tool-Ausführung.
- Verworfen, weil für dieselbe fachliche Wirkung unnötige Kosten und Komplexität entstehen.

### Alternative 3
- Asynchrone Ausführung der Tool-Calls über Hintergrundprozesse oder Queues.
- Verworfen, weil dadurch Debugging schwieriger wird und versteckte Nebenläufigkeit entsteht.

### Alternative 4
- Unabhängige, manuell gestartete Einzel-Tools ohne zentralen Orchestrator.
- Verworfen, weil abhängige Änderungen dann nicht kontrolliert im selben Zyklus sichtbar werden.

### Alternative 5
- Rein ereignisgetriebene Aktualisierung ohne periodischen Loop.
- Verworfen, weil die zentrale Ablaufsteuerung und feste Reihenfolge damit verloren gehen.

## Konsequenzen
- positiv: Der Ablauf bleibt deterministisch und gut nachvollziehbar.
- positiv: Normale LLM-Antworten werden nicht durch Tool-/Function-Calling blockiert.
- positiv: Die Architektur ist vereinfacht (kein separater Orchestrator-Layer).
- negativ: Blockierende LLM-Calls verlängern einen Scheduler-Zyklus und begrenzen die Parallelität.
- offen: Ob künftig partielle Asynchronisierung, adaptive Intervalle oder eine stärkere Entkopplung der Jobs nötig werden.

## Annahmen
- `rate_limit_seconds` begrenzt die Häufigkeit einzelner Job-Läufe.
- Periodische Scheduler-Zyklen allein erzeugen keine neuen Job-Läufe ohne vorherige fachliche Vormerkung.

## Offene Fragen
- Ob die aktuelle Reihenfolge und Synchronität bei steigender Last ausreichend bleiben.

## Referenzen
- `engine/tools/scheduler.py`
- `engine/tools/abstract_job.py`, `engine/tools/etm_job.py`, `engine/tools/state_job.py`, `engine/tools/scene_job.py`, `engine/tools/image_job.py`
- `engine/web/app.py`
