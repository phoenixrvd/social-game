---
state: implemented
---

# SG-025: Einheitliches Vorschauverhalten generierter Bilder

## Kontext
Mehrere Erstellungsdialoge in der Web-GUI kombinieren die Auswahl eines Referenzbilds mit einer Bildvorschau.
Diese Anforderung beschreibt das fachlich einheitliche Klickverhalten der Vorschau für Dialogzustände ohne und mit erzeugtem Vorschaubild.

## Annahmen
- Die Anforderung gilt für Dialoge, in denen ein Referenzbild ausgewählt und ein erzeugtes Vorschaubild angezeigt werden kann.
- Die vergrößerte Vorschau orientiert sich fachlich am bestehenden Verhalten der Bildvorschau im Chat.

## Offene Fragen
- Keine

## Anforderungen

### Einheitliches Klickverhalten der Bildvorschau
**Typ:** Funktional  
**Beschreibung:** Das System muss in Dialogen mit Referenzbild und Bildvorschau ein einheitliches Klickverhalten für den aktuellen Bildzustand bereitstellen.  
**Akzeptanzkriterien:**
- Solange noch kein erzeugtes Vorschaubild vorhanden ist, öffnet ein Klick auf die Vorschau die Auswahl eines Referenzbilds.
- Die Auswahl eines Referenzbilds erlaubt auf Geräten mit Kamera die Aufnahme eines neuen Bilds, sofern Browser und Gerät dies unterstützen.
- Sobald ein erzeugtes Vorschaubild vorhanden ist, öffnet ein Klick auf die Vorschau eine vergrößerte Overlay-Vorschau.
- Solange ein erzeugtes Vorschaubild vorhanden ist, öffnet derselbe Klick keine Auswahl eines Referenzbilds.
- Die Overlay-Vorschau entspricht fachlich dem Verhalten der Bildvorschau im Chat.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`
