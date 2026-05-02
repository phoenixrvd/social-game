---
state: implemented
---

# ADR-001: Test-Strategie

## Status
implemented

## Kontext
- Das Projekt nutzt viele `pytest`-Tests und Abhängigkeiten wie Dateisystem, LLM-Aufrufe und Zeitbezug.
- Tests sollen das Verhalten der Anwendung prüfen, nicht die Verdrahtung eines Mock-Setups oder das Workspace-`.data` verändern.

## Entscheidung
- Tests werden bevorzugt mit echten Implementierungen und explizit injizierten Abhängigkeiten geschrieben; Mock-Frameworks werden nicht verwendet, und `monkeypatch` ist nur als gezielte Ausnahme erlaubt, um globale Pfade oder dynamisches Datum zu überschreiben.
- Pro Verhalten gilt die harte Minimalregel: genau ein hochwirksamer Regressionstest pro Failure-Signalpfad; redundante Varianten mit gleichem Setup und gleicher Aussage werden entfernt.
- Storage-Schicht-Tests folgen der Schichttrennung aus ADR-009:
  - **Store-Tests** prüfen Persistenzlogik und Domain/Persistenz-Mapping isoliert gegen `tmp_path` (JSONL, SQLite).
  - **Domain-/DTO-Modell-Tests** prüfen Validierung und Repräsentationslogik ohne Dateisystembezug.
  - **Service-Tests** greifen ausschließlich über `storage.*` zu; direkte Instanziierung von Stores oder Datei-Adaptern ist in Tests nicht erlaubt.

## Begründung
- Echte Implementierungen prüfen das Verhalten der Anwendung statt die Konfiguration eines Mock-Setups.
- Dateisystembasierte Komponenten können mit injizierten Pfaden gegen `tmp_path` getestet werden.
- LLM-Aufrufe sind extern, nicht deterministisch und langsam; dafür reicht ein einfacher Ersatz mit demselben Vertrag.
- Zeitabhängigkeiten lassen sich über injizierbare Parameter oder gezieltes Überschreiben des dynamischen Datums testbar machen.
- Globale Pfade und dynamisches Datum sind eng an den Prozesskontext gebunden; dafür ist gezieltes `monkeypatch` ausreichend, ohne die grundsätzliche Ausrichtung auf echte Implementierungen aufzugeben.
- Testläufe sollen gegenüber dem Workspace-`.data` nebenwirkungsfrei bleiben.
- Die Suite bleibt absichtlich klein: zusätzliche Tests sind nur zulässig, wenn sie einen neuen Risikobereich oder ein neues Fehlersignal abdecken.
- Die Schichttrennung aus ADR-009 (Store / Domain-Modell / Storage-Knoten / Service) ermöglicht fokussierte, stabile Tests pro Schicht ohne Überlappung.

## Alternativen
### Alternative 1
- Mock-Frameworks wie `unittest.mock` oder `pytest-mock` breit einsetzen.
- Verworfen, weil damit leicht Interaktionen und Konfigurationen statt des echten Anwendungsverhaltens getestet werden.

### Alternative 2
- `monkeypatch.setattr` auf Modulebene allgemein für beliebige Abhängigkeiten verwenden.
- Verworfen, weil Tests dadurch an Implementierungsdetails gekoppelt werden und bei Refactorings instabiler werden.

### Alternative 3
- Tests gegen das echte Workspace-`.data` und echte externe LLM-Aufrufe ausführen.
- Verworfen, weil dadurch Seiteneffekte, Nichtdeterminismus und langsame Testläufe entstehen.

## Konsequenzen
- positiv: Tests bleiben direkt lesbar und verhaltensorientiert.
- positiv: Globale Pfade und dynamisches Datum können in Tests gezielt und einfach kontrolliert werden.
- positiv: Schnellere Testläufe mit höherem Signal-Rausch-Verhältnis durch weniger Duplikate.
- positiv: Store- und Domain-Tests sind vollständig dateisystemunabhängig und laufen schnell und stabil.
- negativ: Der Code braucht weiterhin explizite Injektionspunkte für Dateisystem, LLM-Grenzen und Zeitbezug, sofern keine enge globale Ausnahme vorliegt.
- offen: Der zulässige Einsatz von `monkeypatch` bleibt auf globale Pfade und dynamisches Datum begrenzt.
- offen: Bei neuen Anforderungen muss aktiv entschieden werden, ob ein bestehender Test erweitert statt ein neuer Test hinzugefügt wird.

## Annahmen
- Dateisystempfade und Zeitbezug können über Parameter injiziert werden oder liegen als globale Pfade beziehungsweise dynamisches Datum vor, die gezielt überschrieben werden können.
- LLM-Aufrufe bleiben die einzige externe Grenze, die in Tests durch einfache Callables ersetzt wird.

## Offene Fragen
- Keine

## Referenzen
- ADR-009: Storage-Architektur und Zugriffsschicht
- `tests/`
- `engine/config.py`

