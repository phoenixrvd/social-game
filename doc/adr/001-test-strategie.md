# ADR 001: Test-Strategie

**Status:** Akzeptiert  
**Datum:** 2026-03-15

## Kontext

Tests sollen sicherstellen, dass die Anwendung korrekt funktioniert. Eine haeufige Falle ist es,
stattdessen das Mock-Framework oder die eigene Verdrahtung zu testen. Das gibt falsches Vertrauen:
Ein Test, der nur prueft, ob `mock.assert_called_once_with(...)` klappt, sagt nichts darueber aus,
ob die Anwendung in der echten Ausfuehrung das Richtige tut.

Das Projekt hat Abhaengigkeiten, die in Tests substituiert werden muessen:

- **Filesystem**: Repositories lesen/schreiben Dateien → durch `tmp_path` loesbar.
- **LLM-Aufrufe**: Externe API, nicht deterministisch, langsam → echter Ersatz noetig.
- **Zeit** (`datetime.now`): Beeinflusst Trigger-Logik → durch injizierbare Parameter loesbar.

## Entscheidung

### 1. Echte Implementierungen bevorzugen

Wo immer moeglich werden echte Klassen mit echten Daten getestet.
Filesystem-basierte Repositories akzeptieren `base_dir` als Parameter und koennen damit
gegen `tmp_path` laufen. Es wird kein Fake benoetigt.

```python
# gut
short_repo = ShortMemoryRepository(base_dir=tmp_path / "npcs")
short_repo.append_turn("vika", "Hallo", "Hey")
service = LtmService(short_memory_repo=short_repo, ..., summarizer=lambda p: "ltm")

# schlecht
monkeypatch.setattr(module, "ShortMemoryRepository", FakeShortMemoryRepository)
```

### 2. LLM-Grenze mit einfachen Callables schliessen

LLM-Aufrufe sind der einzige legitime Grund fuer einen Ersatz. Kein Mock-Framework –
stattdessen eine einfache Python-Funktion, die denselben Vertrag erfuellt:

```python
# gut
def fake_summarizer(prompt: str) -> str:
    return "updated ltm"

service = LtmService(..., summarizer=fake_summarizer)

# schlecht
mock_summarizer = MagicMock(return_value="updated ltm")
service = LtmService(..., summarizer=mock_summarizer)
mock_summarizer.assert_called_once()  # testet das Mock, nicht die Anwendung
```

### 3. Kein Monkeypatching

`monkeypatch.setattr` auf Modulebene ersetzt Objekte zur Laufzeit und koppelt Tests an
Implementierungsdetails (Importpfade, Modul-Attribute). Das bricht bei Refactorings und
verdeckt, was wirklich getestet wird.

Wenn ein Test ohne Monkeypatching nicht schreibbar ist, ist das ein Hinweis darauf,
dass der betroffene Code schwer testbar ist und refactored werden sollte (z. B. durch
Dependency Injection statt hartcodierter Abhaengigkeiten).

### 4. Keine Mock-Frameworks

`unittest.mock`, `pytest-mock` und aehnliche Frameworks sind im Projekt nicht erlaubt.
Weder `MagicMock`, `patch`, noch `AsyncMock`.

### 5. Injizierbare Parameter statt Mocking fuer Zeitabhaengigkeiten

Funktionen, die von `datetime.now` abhaengen, nehmen `now: datetime | None = None`
als Parameter entgegen. Tests uebergeben einen fixen Zeitstempel – kein Patching noetig.

```python
# gut
service.update_if_needed("vika", now=datetime(2026, 1, 1, tzinfo=UTC))

# schlecht
monkeypatch.setattr("engine.ltm_service.datetime", fake_datetime)
```

### 6. Tests veraendern niemals das Workspace-`.data`

Wenn ein Service standardmaessig nach `/.data` schreibt, muessen Tests eine injizierte Abhaengigkeit oder einen expliziten Testpfad nutzen, damit das Workspace-`.data` unveraendert bleibt.

## Konsequenzen

- Tests sind direkt lesbar: Man sieht, welche echten Objekte beteiligt sind.
- Refactorings brechen keine Tests durch fehlerhafte Mock-Konfigurationen.
- Fehler in der echten Implementierung (z. B. Repository-Serialisierung) werden
  in Service-Tests sichtbar, nicht erst zur Laufzeit.
- LLM-Aufrufe bleiben der einzige Punkt, an dem ein Ersatz noetig ist – das ist
  transparent und minimiert den Fake-Anteil auf einen einzigen Parameter.
- Bestehende Tests mit Monkeypatching (z. B. in `test_cli.py` und den Updater-Tests wie
  `test_state_update_service.py`) werden bei Gelegenheit schrittweise auf echte
  Implementierungen umgestellt. Die Updater-Klassen unterstuetzen aktuell keine
  vollstaendige Dependency Injection fuer LLM-Callables, was Monkeypatching in diesen
  Tests noch erfordert.
- Testlaeufe sind nebenwirkungsfrei gegen das Workspace-`.data`; lokale Laufzeitdaten bleiben stabil.

