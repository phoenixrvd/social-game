---
state: defined
---

# ADR-006: Rolling Releases ohne Kompatibilitätsschichten

## Status
defined

## Kontext
- Das Projekt wird aktuell intern ohne Dritt-Nutzer betrieben und Änderungen werden als Rolling Releases ausgerollt.
- Kurzfristige Kompatibilitätshinweise und Alias-Artefakte bei Umbenennungen erhöhen den Pflegeaufwand und machen kanonische Quellen unklar.

## Entscheidung
- Im aktuellen Produktstadium werden keine Kompatibilitätsschichten eingeführt; Umbenennungen werden direkt und vollständig in Code, Dokumentation und Tests übernommen.

## Begründung
- Eine einzige kanonische Quelle pro Verantwortung ist konsistenter und einfacher wartbar.
- Alias-Dateien, Deprecated-Hinweise und Dual-Naming erhöhen die Komplexität ohne erkennbaren Nutzen für das aktuelle interne Produktstadium.
- Rolling Releases erlauben direkte Bereinigung von Namen und Verträgen.

## Alternativen
### Alternative 1
- Kompatibilitätsschichten bei Umbenennungen pflegen.
- Verworfen, weil zusätzliche Alias-Artefakte und Hinweise den Pflegeaufwand erhöhen.

### Alternative 2
- Historische Namen und Mappings in der kanonischen Dokumentation weiterführen.
- Verworfen, weil dadurch der aktuelle Standard unklar wird.

### Alternative 3
- Dual-Naming für eine Übergangszeit zulassen.
- Verworfen, weil dadurch keine eindeutige kanonische Quelle entsteht.

## Konsequenzen
- positiv: Die Architektur- und Namensbereinigung bleibt schnell und wartungsarm.
- negativ: Interne Breaking Changes müssen pro Release unmittelbar nachgezogen werden.
- offen: Ob bei künftigem externem Nutzerbetrieb ein anderer Umgang mit Umbenennungen nötig wird.

## Annahmen
- Das Projekt bleibt aktuell intern ohne Dritt-Nutzer.
- README, Anforderungen und CLI-Hilfetexte beschreiben den aktuellen Stand als alleinigen Standard.

## Offene Fragen
- Ob diese Entscheidung bei künftigem externem Nutzerbetrieb angepasst werden muss.

## Referenzen
- Keine

