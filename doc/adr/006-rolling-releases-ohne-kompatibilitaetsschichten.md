# ADR 006: Rolling Releases ohne Kompatibilitaetsschichten

**Status:** Akzeptiert
**Datum:** 2026-03-16

## Kontext

Das Projekt wird aktuell intern ohne Dritt-Nutzer betrieben.
Aenderungen werden als Rolling Releases ausgerollt.

In den letzten Iterationen sind bei Umbenennungen (z. B. Prompt-Dateien) kurzfristige
Kompatibilitaets-Hinweise und Alias-Artefakte entstanden. Diese Zwischenlagen erhoehen
Pflegeaufwand und sorgen fuer unklare kanonische Quellen.

## Entscheidung

Wir fuehren im aktuellen Produktstadium **keine Kompatibilitaetsschichten** ein.

Konkret:

- Es gibt pro Verantwortung genau **eine kanonische Quelle** (Datei, Kommando, Vertrag).
- Umbenennungen werden direkt und vollstaendig durchgezogen (Code, Doku, Tests).
- Deprecated-Hinweise, Alias-Dateien und Dual-Naming werden nicht gepflegt.
- Kanonische Nutzerdokumentation beschreibt ausschließlich den aktuellen Stand, nicht
  alte Namen, Migrationspfade oder Legacy-Kommandos.
- Falls ein Rename notwendig ist, wird die Zielbenennung unmittelbar als alleiniger
  Standard dokumentiert.

## Konsequenzen

- Weniger Komplexitaet und geringerer Wartungsaufwand.
- Schnellere Architektur- und Namensbereinigung im PoC/Fruehprodukt.
- Breaking Changes sind intern akzeptiert und werden pro Release bewusst nachgezogen.
- README, Requirements und CLI-Help-Texte enthalten keine historischen Mapping-Listen,
  solange kein externer Migrationsvertrag vereinbart wurde.
- Bei kuenftigem externem Nutzerbetrieb ist diese ADR neu zu bewerten.

