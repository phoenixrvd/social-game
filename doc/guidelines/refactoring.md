# Refactoring

## Grundregeln

- [BLOCKER] Komplexität bei jeder Änderung reduzieren, wenn risikofrei möglich
- [BLOCKER] Keine Kompatibilitätslayer einführen, bestehende Schnittstellen direkt anpassen

## Konstanten

- [BLOCKER] Globale Konstanten entfernen, wenn sie nicht mehr als zweimal im Modul verwendet werden
- [WARNING] Unklare Literale lokal benennen statt global auszulagern