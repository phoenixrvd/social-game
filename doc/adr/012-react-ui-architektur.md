---
state: accepted
---

# ADR-012: React-UI-Architektur

## Status
accepted

## Kontext
- Die Web-GUI wurde von der alten gemischten Komponentenstruktur auf React migriert.
- Die UI nutzt Backend-Endpunkte über Orval-generierte Clients und React Query für Serverdaten.
- Die Oberfläche enthält mehrere fachliche Bereiche wie Chat, Composer, Szenenbild, Options-Panels und Entity-Editoren.
- Ohne verbindliche Grenze zwischen Datenfluss und Rendering entstehen schnell gemischte Komponenten mit API-, Router-, Query- und Layout-Logik.

## Entscheidung
- Features und Options-Panels werden grundsätzlich in `*Container.tsx` und `*View.tsx` getrennt.
- Container enthalten Datenzugriff, Commands, Router-Zugriffe, React-Query-Hooks, lokalen UI-State, Nebenwirkungen und Props-Mapping.
- Views erhalten vollständige Props, fertige URLs und Callback-Funktionen. Sie enthalten keine API-Aufrufe, keine React-Query-Hooks, keine Command-Hooks und keine Router-Hooks außer `Link`/`NavLink` mit fertigen URLs.
- Feature- und Panel-Container sollen im Regelfall nur die zugehörige View direkt rendern.
- Reine Shared-UI-Komponenten brauchen keine Container/View-Trennung, solange sie keine fachliche Daten-, Router-, Query- oder Command-Logik enthalten.
- Medien- und API-URLs werden nicht in Views per String zusammengesetzt, sondern kommen aus Orval-URL-Funktionen oder zentralen Frontend-Helpern.

## Begründung
- Eine pauschale Trennung für Features und Options-Panels reduziert Grenzfalldiskussionen und macht Reviews einfacher.
- Views bleiben test- und wartbar, weil sie nur Rendering und einfache UI-Bedingungen enthalten.
- Container können Datenfluss, Pending-Zustände, Fehlerbehandlung und Navigation bündeln, ohne Layoutdetails zu vermischen.
- Der zusätzliche Datei-Overhead ist gering gegenüber dem Nutzen einer einheitlichen Struktur.
- Shared-UI-Komponenten bleiben leichtgewichtig und werden nicht durch unnötige Boilerplate aufgebläht.

## Alternativen
### Alternative 1
- Container/View-Trennung nur bei komplexen Komponenten.
- Verworfen, weil dadurch wieder uneinheitliche Grenzfälle entstehen und Datenlogik schrittweise in Views einsickern kann.

### Alternative 2
- Jede Komponente bekommt pauschal Container und View.
- Verworfen, weil reine Shared-UI-Bausteine ohne fachliche Daten- oder Nebenwirkungslogik dadurch unnötig aufgebläht würden.

## Konsequenzen
- positiv: Einheitliche Feature-Struktur in `engine/web/react/`.
- positiv: Keine API-, Query- oder Command-Abhängigkeiten in View-Komponenten.
- positiv: Bessere Nachvollziehbarkeit von Datenfluss, Nebenwirkungen und Rendering.
- negativ: Mehr Dateien und Props-Typen pro Feature.
- offen: Wenn ein Container mehr als reines Props-Mapping und einen direkten View-Aufruf enthält, muss geprüft werden, ob ein kleiner Feature-Hook oder weiterer Container sinnvoll ist.

## Annahmen
- Die React-App bleibt der aktive Frontend-Stack.
- Orval bleibt die einzige API-Client-Schicht für typisierte Backend-Endpunkte.

## Offene Fragen
- Keine

## Referenzen
- `UI_REIMPLEMENTATION_PLAN.md`
- `doc/requirements/sg-011-web-gui.md`
- `doc/adr/007-ui-architektur-mit-web-components.md`
