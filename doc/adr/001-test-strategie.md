---
state: defined
---

# ADR-001: Test-Strategie

## Status
defined

## Kontext
- Das Projekt nutzt viele `pytest`-Tests und Abhängigkeiten wie Dateisystem, LLM-Aufrufe und Zeitbezug.
- Tests sollen das Verhalten der Anwendung prüfen, nicht die Verdrahtung eines Mock-Setups oder das Workspace-`.data` verändern.

## Entscheidung
- Tests werden bevorzugt mit echten Implementierungen und explizit injizierten Abhängigkeiten geschrieben; Mock-Frameworks werden nicht verwendet, und `monkeypatch` ist nur als gezielte Ausnahme erlaubt, um globale Pfade oder dynamisches Datum zu überschreiben.

## Begründung
- Echte Implementierungen prüfen das Verhalten der Anwendung statt die Konfiguration eines Mock-Setups.
- Dateisystembasierte Komponenten können mit injizierten Pfaden gegen `tmp_path` getestet werden.
- LLM-Aufrufe sind extern, nicht deterministisch und langsam; dafür reicht ein einfacher Ersatz mit demselben Vertrag.
- Zeitabhängigkeiten lassen sich über injizierbare Parameter oder gezieltes Überschreiben des dynamischen Datums testbar machen.
- Globale Pfade und dynamisches Datum sind eng an den Prozesskontext gebunden; dafür ist gezieltes `monkeypatch` ausreichend, ohne die grundsätzliche Ausrichtung auf echte Implementierungen aufzugeben.
- Testläufe sollen gegenüber dem Workspace-`.data` nebenwirkungsfrei bleiben.

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
- negativ: Der Code braucht weiterhin explizite Injektionspunkte für Dateisystem, LLM-Grenzen und Zeitbezug, sofern keine enge globale Ausnahme vorliegt.
- offen: Der zulässige Einsatz von `monkeypatch` bleibt auf globale Pfade und dynamisches Datum begrenzt.

## Annahmen
- Dateisystempfade und Zeitbezug können über Parameter injiziert werden oder liegen als globale Pfade beziehungsweise dynamisches Datum vor, die gezielt überschrieben werden können.
- LLM-Aufrufe bleiben die einzige externe Grenze, die in Tests durch einfache Callables ersetzt wird.

## Offene Fragen
- Keine

## Referenzen
- `tests/`
- `engine/config.py`

