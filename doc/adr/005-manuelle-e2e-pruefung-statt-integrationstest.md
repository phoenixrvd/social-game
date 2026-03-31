# ADR 005: Voruebergehend manuelle E2E-Pruefung statt vollem Integrationstest

**Status:** Akzeptiert  
**Datum:** 2026-03-15

## Kontext

Ein echter End-to-End-Integrationstest fuer den Gesamtfluss
`chat -> STM -> State/LTM Side-Effects` waere grundsaetzlich wuenschenswert.

In der aktuellen Projektphase ist dieser Test jedoch unverhaeltnismaessig teuer:

- der Chat-Loop ist stark interaktiv,
- mehrere Schritte haengen an LLM-Aufrufen oder deren Ersatzgrenzen,
- die Produktlogik befindet sich noch in einer fruehen PoC-/Refactoring-Phase,
- ein grosser Integrationstest wuerde momentan mehr Testverkabelung als Erkenntnis erzeugen.

Das Projekt folgt laut [ADR 001](./001-test-strategie.md) dem Grundsatz,
moeglichst die Anwendung statt Mocking-Infrastruktur zu testen.
Ein frueher E2E-Test fuer den kompletten Chat-Flow wuerde aktuell entweder
zu instabil oder zu stark kuenstlich verdrahtet ausfallen.

## Entscheidung

Ein vollstaendiger automatisierter End-to-End-Integrationstest fuer den Gesamtfluss
wird **voruebergehend nicht umgesetzt**.

Stattdessen gilt in der aktuellen Phase:

- Services und Repositories werden weiterhin gezielt automatisiert getestet.
- Der Gesamtfluss wird voruebergehend **manuell** geprueft.
- Die manuelle Pruefung umfasst mindestens:
  - Chat mit einem NPC starten
  - Spieler- und NPC-Nachrichten im STM verifizieren
  - automatisches State-Update beobachten
  - automatisches LTM-Update beobachten
  - Persistenz in `.data/` kontrollieren
  - Logging-Ausgaben der beteiligten Services pruefen

## Konsequenzen

- Die Testabdeckung bleibt fokussiert auf stabile, wartbare Einheiten.
- Es wird bewusst akzeptiert, dass der Gesamtfluss vorerst manuell validiert wird.
- Sobald der Chat-Loop stabiler und die Systemgrenzen klarer sind, wird die Entscheidung neu bewertet.
- Ein spaeterer Integrationstest soll dann moeglichst mit echten Repositories und minimalen Ersatzgrenzen aufgebaut werden.

