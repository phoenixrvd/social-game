# ADR 003: Synchroner Update-Orchestrator

**Status:** Akzeptiert  
**Datum:** 2026-03-25

## Kontext

Das System aktualisiert mehrere Zustände:

- LTM
- State
- Scene
- Image

Updates basieren auf STM, bestehendem Kontext und spezialisierten Prompt-Templates.  
Mit SG-008 existiert ein Orchestrator, der beim Start der Web-GUI (`sg web`) automatisch mitläuft.

Ziel ist:

- deterministisches Verhalten
- Debuggbarkeit
- keine versteckten Hintergrundprozesse

## Entscheidung

Alle Updates werden **synchron innerhalb eines periodischen Orchestrator-Loops** ausgeführt.

Pro Updater:

1. `schedule()` prüft Zeit + neue Nachrichten + Regeln bzw. Trigger intern
2. der Prompt wird direkt aus den relevanten Daten aufgebaut
3. der LLM-Call wird **blockierend** ausgeführt
4. das Ergebnis wird persistiert
5. abhängige Folgeaktionen werden direkt ausgelöst

## Orchestrator

- Lauf: automatisch im Web-Lifecycle von `sg web`
- Reihenfolge:
    1. LTM
    2. Scene
    3. State
    4. Image

→ wichtig für Abhängigkeiten (Image ← Scene/State)

## Konsequenzen

**Vorteile**
- deterministisch
- gut debuggbar
- keine Race Conditions
- klare Update-Trigger in `schedule()` ohne verteilte Zusatzlogik

**Nachteile**
- höhere Latenz pro Zyklus
- keine Parallelisierung

## Design-Regeln

- `schedule()` verhindert unnötige LLM-Calls über interne Aktivierungsbedingungen
- alle vier Updater führen ihren Prompt-Schritt direkt aus, sobald die jeweiligen Aktivierungsbedingungen erfüllt sind
- `scene`, `state` und `ltm` reagieren auf neue Nachrichten seit dem letzten Check
- `image` reagiert auf einen expliziten Run-Trigger aus `scene` bzw. `state`
- `image` erzeugt nur dann ein neues Bild, wenn der frisch erzeugte Prompt hinreichend vom zuletzt gespeicherten Prompt abweicht (Exact-/Fuzzy-/Token-Ähnlichkeitsprüfung)
- Image wird erst nach `scene` und `state` eingeplant, damit abhängige Änderungen im selben Orchestrator-Zyklus sichtbar werden

## Zukunft

- partielle Asynchronisierung möglich
- adaptive Intervalle / Batching
- stärkere Entkopplung der Updater

## Fazit

Synchron + periodisch = **kontrollierte Automatisierung mit maximaler Nachvollziehbarkeit**