---
state: implemented
---

# ADR-003: Synchroner Update-Orchestrator

## Status
implemented

## Kontext
- Das System aktualisiert ETM, State, Scene und Image auf Basis von STM, bestehendem Kontext und spezialisierten Prompt-Templates.
- Beim Start von `sg web` läuft ein Orchestrator automatisch mit; Ziel sind deterministisches Verhalten, Debuggbarkeit und keine versteckten Hintergrundprozesse.

## Entscheidung
- Der Update-Orchestrator läuft synchron und periodisch im Web-Lifecycle von `sg web`; die Updater werden fachlich in der Reihenfolge ETM, Scene, State und Image ausgeführt und erledigen Aktivierungsprüfung, Prompt-Aufbau, blockierenden LLM-Call, Persistierung und direkte Folgeaktionen im selben Zyklus.
- Die technische Updater-ID für ETM kann vorübergehend aus der bisherigen Implementierung stammen, solange die fachliche Zielverantwortung klar bleibt.

## Begründung
- Synchrones Ausführen erhöht Nachvollziehbarkeit und Determinismus.
- Die feste Reihenfolge berücksichtigt Abhängigkeiten, insbesondere für `image` nach `scene` und `state`.
- Interne Aktivierungsbedingungen in `schedule()` vermeiden unnötige LLM-Calls.
- Der automatische Start im Web-Lifecycle verhindert separate manuelle Startschritte.

## Alternativen
### Alternative 1
- Asynchrone Ausführung der Updater über Hintergrundprozesse oder Queues.
- Verworfen, weil dadurch Debugging schwieriger wird und versteckte Nebenläufigkeit entsteht.

### Alternative 2
- Unabhängige, manuell gestartete Einzelupdates ohne zentralen Orchestrator.
- Verworfen, weil abhängige Änderungen dann nicht kontrolliert im selben Zyklus sichtbar werden.

### Alternative 3
- Rein ereignisgetriebene Aktualisierung ohne periodischen Loop.
- Verworfen, weil die zentrale Ablaufsteuerung und feste Reihenfolge damit verloren gehen.

## Konsequenzen
- positiv: Der Ablauf bleibt deterministisch und gut nachvollziehbar.
- negativ: Blockierende LLM-Calls verlängern einen Zyklus und begrenzen die Parallelität.
- offen: Ob künftig partielle Asynchronisierung, adaptive Intervalle oder eine stärkere Entkopplung der Updater nötig werden.

## Annahmen
- `schedule()` kapselt die Aktivierungsbedingungen je Updater.
- `image` hängt fachlich von Änderungen in `scene` und `state` ab.

## Offene Fragen
- Ob die aktuelle Reihenfolge und Synchronität bei steigender Last ausreichend bleiben.

## Referenzen
- `engine/updater/schedule.py`
- `engine/web/app.py`
