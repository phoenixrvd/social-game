---
state: defined
---

# ADR-005: Manuelle E2E-Prüfung statt vollständigem Integrationstest

## Status
defined

## Kontext
- Ein automatisierter End-to-End-Integrationstest für den Gesamtfluss `chat -> STM -> State/LTM Side-Effects` wäre grundsätzlich wünschenswert.
- In der aktuellen Projektphase ist dieser Test unverhältnismäßig teuer, weil der Chat-Loop stark interaktiv ist, mehrere Schritte an LLM-Aufrufen oder deren Ersatzgrenzen hängen und die Produktlogik noch in einer frühen PoC- und Refactoring-Phase ist.

## Entscheidung
- Der Gesamtfluss `chat -> STM -> State/LTM Side-Effects` wird aktuell manuell als E2E-Prüfung validiert statt durch einen vollständigen automatisierten Integrationstest.

## Begründung
- Ein vollständiger E2E-Test würde derzeit mehr Testverkabelung als Erkenntnis erzeugen.
- Ein früher Gesamtflusstest wäre aktuell entweder instabil oder stark künstlich verdrahtet.
- Services, Repositories und weitere Einheiten können weiterhin gezielt automatisiert getestet werden.
- Die manuelle Prüfung deckt den realen Ablauf einschließlich Persistenz in `.data/` und Logging-Ausgaben der beteiligten Services ab.

## Alternativen
### Alternative 1
- Den vollständigen automatisierten End-to-End-Integrationstest sofort umsetzen.
- Verworfen, weil der Aufwand in der aktuellen Projektphase unverhältnismäßig hoch ist.

### Alternative 2
- Ausschließlich bestehende automatisierte Einzeltests ohne manuelle Gesamtprüfung verwenden.
- Verworfen, weil der zusammenhängende Gesamtfluss damit nicht als End-to-End-Ergebnis geprüft wird.

## Konsequenzen
- positiv: Die automatisierte Testabdeckung bleibt auf stabile und wartbare Einheiten fokussiert.
- negativ: Für den Gesamtfluss gibt es vorerst keine automatisierte Regressionsabsicherung.
- offen: Die Entscheidung wird neu bewertet, sobald der Chat-Loop stabiler und die Systemgrenzen klarer sind.

## Annahmen
- Services, Stores, CLI, Web-App und Updater werden weiterhin automatisiert getestet.
- Die manuelle Prüfung umfasst mindestens Chat-Start, STM-Prüfung, Beobachtung von State- und LTM-Updates, Kontrolle der Persistenz in `.data/` und Prüfung der Logging-Ausgaben.

## Offene Fragen
- Ab wann der Chat-Loop und die Systemgrenzen stabil genug für einen vollständigen automatisierten Gesamtflusstest sind.

## Referenzen
- `doc/adr/001-test-strategie.md`
- `tests/`

