# Refactoring

- Reduziere Komplexität bei jeder Änderung mit, wenn es ohne Mehr-Risiko möglich ist.
- Baue keine Kompatibilitätslayer bei Refactorings ein, sondern aktualisiere bestehende Schnittstellen direkt.
- Führe globale Konstanten zurück auf direkte Literale, wenn sie nicht mehr als zweimal im Modul verwendet werden.
- Wenn Literale ohne Kontext unklar sind, benenne sie lokal statt sie unnötig global auszulagern.
