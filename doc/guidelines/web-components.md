# Web Components

## Lifecycle

- [BLOCKER] `connectedCallback()` und `disconnectedCallback()` nicht aufgrund von "unused"-Warnungen entfernen
- [BLOCKER] Lifecycle-Hooks nur verwenden, wenn sie tatsächliche Initialisierung oder Cleanup durchführen
- [BLOCKER] Keine zusätzlichen Abstraktionen oder Interfaces zur Absicherung von Lifecycle-Hooks

## Registrierung

- [WARNING] Guard-Checks bei `customElements.define` in Kurzform (`||`) schreiben

## Komponenten-Grenzen

- [BLOCKER] Kein Zugriff auf internes DOM von Child-Komponenten (`querySelector` verboten)
- [BLOCKER] Kommunikation ausschließlich über öffentliche APIs (Properties/Methoden) und `CustomEvent`s

## DOM-Struktur

- [BLOCKER] Pflicht-Elemente der eigenen Komposition nicht defensiv prüfen
- [BLOCKER] Fehlende Pflicht-Elemente sind Implementierungsfehler und dürfen nicht durch Guards oder frühe Returns verborgen werden

## Initialisierung

- [BLOCKER] Interne DOM-Struktur bei Nutzung von `innerHTML` direkt in `connectedCallback()` aufbauen
- [BLOCKER] Keine Reinitialisierungs-Guards (`_initialized`, Sentinels)

## DOM-Zugriff

- [BLOCKER] Pflicht-Elemente nach Initialisierung einmalig cachen (z. B. `this.$`)
- [BLOCKER] Wiederholte `querySelector`-Aufrufe vermeiden
- [BLOCKER] Keine Proxy-Getter für DOM-Elemente
- [BLOCKER] DOM-Elemente nicht auf Instanzebene speichern, wenn sie nur innerhalb einer Methode verwendet werden

## Events

- [BLOCKER] Keine Hilfsfunktionen, die nur `dispatchEvent(...)` weiterreichen
- [BLOCKER] Events direkt über die Komponente dispatchen
- [BLOCKER] Event-Handler direkt bei Registrierung binden (`bind(this)`)
- [BLOCKER] Keine Proxy-Handler oder gebundene Zwischenvariablen für Event-Handler
- [WARNING] Listener-Management-Pattern (z. B. zentrale Listener-Listen) nur bei echtem Bedarf einsetzen