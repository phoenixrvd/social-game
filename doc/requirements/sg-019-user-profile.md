---
state: implemented
---

# SG-019: User Profile

## Kontext
Das System verwaltet ein User Profile als langfristige Sicht des aktiven NPC auf den Spieler. Das Profil
enthält manuell hinterlegte, stabile Informationen und wird als Kontext im Dialog verwendet. Die Pflege in
der Web-GUI erfolgt über Player-Avatare, deren Beschreibung das aktive User Profile bereitstellt.

## Annahmen
- Ein Avatar-Wechsel während einer laufenden Session ist erlaubt.
- Inkonsistente Dialogkontexte nach einem Wechsel werden bewusst akzeptiert.

## Offene Fragen
- Keine

## Anforderungen

### Bereitstellung und Nutzung im Dialogkontext
**Typ:** Funktional  
**Beschreibung:** Das System muss ein User Profile als optionalen Langzeitkontext über den Spieler im Dialogkontext bereitstellen.  
**Akzeptanzkriterien:**
- Ein User Profile kann leer sein.
- Das System funktioniert auch ohne vorhandenes User Profile.
- Das aufgelöste User Profile kann im NPC-Dialogkontext berücksichtigt werden.
- Das User Profile kann Interpretation, Ton, Nähe und Verhalten der NPC-Antwort beeinflussen.
- Aktuelle Nachrichten im Short-Term-Memory haben bei Widersprüchen Vorrang vor Profilinformationen.
- Das User Profile wird nicht explizit als eigener Dialoginhalt ausgegeben.
**Referenzen:** `doc/requirements/sg-001-dialogbasierte-interaktionen.md`, `doc/requirements/sg-003-short-term-memory.md`

### Speicherorte des User Profiles
**Typ:** Randbedingung  
**Beschreibung:** Das System muss User Profiles an definierten Speicherorten unterstützen.  
**Akzeptanzkriterien:**
- Das aktive User Profile wird aus der Beschreibung des aktiven Avatars gelesen.
- Mitgelieferte Avatar-Profile liegen unter `avatars/<avatar_id>/description.md`.
- Geänderte und eigene Avatar-Profile liegen unter `.overrides/avatars/<avatar_id>/description.md`.
- Bestehende `user_profile.md`-Dateien können als Legacy-Daten vorhanden sein, werden aber nicht mehr über die Web-GUI gepflegt.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Standard-Avatare
**Typ:** Funktional  
**Beschreibung:** Das System muss mitgelieferte Standard-Avatare bereitstellen, deren Beschreibung das User Profile bildet.  
**Akzeptanzkriterien:**
- Die Standard-Avatare `max` und `erika` existieren unter `avatars/<id>/`.
- Wenn keine Avatar-ID in der Session gespeichert ist, ist `max` aktiv.
- Jeder Avatar besteht aus `character.yaml`, `description.md` und `img.png`.

### Avatar-Auswahl
**Typ:** Funktional  
**Beschreibung:** Das System muss den aktiven Spieleravatar in der Session speichern und wechseln können.  
**Akzeptanzkriterien:**
- Die aktive Auswahl wird als `avatar_id` in `.data/session.yaml` gespeichert.
- Ein Avatar-Wechsel löst keine Scheduler-Jobs und keine NPC- oder Szenenkontextanpassung aus.
- Ungültige gespeicherte Avatar-IDs werden auf den Default-Avatar zurückgesetzt.

### Avatar-Speicherung
**Typ:** Randbedingung  
**Beschreibung:** Das System muss Avatar-Dateien über Default- und Override-Ebenen auflösen.  
**Akzeptanzkriterien:**
- Mitgelieferte Avatare liegen unter `avatars/<id>/`.
- Geänderte und eigene Avatare liegen unter `.overrides/avatars/<id>/`.
- Die Auflösung nutzt Override vor Default.
- Es gibt keine `.data/avatars`-Ebene.
- Es gibt keinen globalen Datei-Fallback auf `avatars/max/<filename>`.

### Priorisierung der Datenschichten
**Typ:** Randbedingung  
**Beschreibung:** Das System muss User Profiles über die bestehende Datei-Überladelogik mit definierter Priorität auflösen.  
**Akzeptanzkriterien:**
- `.overrides/avatars/<avatar_id>/description.md` hat Vorrang vor `avatars/<avatar_id>/description.md`.
- Es gibt keine `.data/avatars`-Ebene.
- Es gibt keinen globalen Fallback auf `avatars/max/description.md` für einzelne Avatar-Dateien.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Manuelle statische Profilpflege
**Typ:** Funktional  
**Beschreibung:** Das System muss das User Profile ausschliesslich als manuell gepflegte, statische Hinterlegung fuehren.  
**Akzeptanzkriterien:**
- Profilinhalte ändern sich nur durch manuelle Avatar-Bearbeitung.
- Ein Dialog allein erzeugt keinen neuen Profilinhalt.
- Ein Dialog allein verändert keinen vorhandenen Profilinhalt.

### Profilgröße
**Typ:** Randbedingung  
**Beschreibung:** Das User Profile ist auf eine sozial realistische und kognitiv handhabbare Größe begrenzt.  
**Begründung (kognitive Psychologie):**
- Miller's Law (1956): Das menschliche Arbeitsgedächtnis hält ~7 ± 2 Einheiten aktiv gleichzeitig.
- Für *bekannte Personen* (Kollegen, Bekannte) werden im Langzeitgedächtnis schätzungsweise 15–25 stabile Fakten aktiv gehalten, die das soziale Verhalten beeinflussen (z. B. Name, Beruf, Familie, Hobbys, Vorlieben, Grenzen, wiederkehrende Themen).
- Enge Beziehungen können 40–100+ Fakten umfassen, aber nur ca. 20–30 davon sind sozial aktiv.
- Ein Limit von 25 Einträgen entspricht damit der oberen Grenze einer „Bekannten/Kollegen"-Beziehung und verhindert unnötigen Ballast.
**Akzeptanzkriterien:**
- Das User Profile enthält in der Regel maximal 25 Einträge.
- Jeder Eintrag entspricht einem stabilen, eigenständigen Fakt im Format `- schluessel: wert`.
- Duplikate oder überholte Einträge werden bei der Fortschreibung entfernt.

### NPC-Perspektive
**Typ:** Randbedingung  
**Beschreibung:** Das System muss das User Profile aus Sicht des aktiven NPC führen.  
**Akzeptanzkriterien:**
- Inhalte beschreiben, was der aktive NPC über den Spieler weiß oder annimmt.
- Unsicherheiten werden als Eindruck formuliert.
- Das User Profile enthält keine externe oder systemische Analyse des Spielers.
- Es wird kein zusätzliches Wissen außerhalb von Profil und Dialog erfunden.
**Referenzen:** `doc/requirements/sg-003-short-term-memory.md`, `doc/requirements/sg-015-episodic-term-memory.md`

### Editierbarkeit in der Web-GUI
**Typ:** Funktional  
**Beschreibung:** Das System muss das User Profile im Bereich „Allgemein“ der Web-GUI über die Avatar-Verwaltung editierbar bereitstellen.  
**Akzeptanzkriterien:**
- Der Bereich ist sichtbar mit der Überschrift `Dein Avatar`.
- Die Avatar-Liste wird nach Anzeigename sortiert.
- Das User Profile ist die Beschreibung des aktiven Avatars.
- Die Bearbeitung wird explizit über `Avatar bearbeiten` in einem eigenen Options-Panel geöffnet.
- Änderungen werden über `Speichern` gespeichert.
- Die Speicherung erfolgt unter `.overrides/avatars/<avatar_id>/description.md`.
- Eigene Avatare können erstellt, bearbeitet und gelöscht werden.
- Standard-Avatare können bearbeitet, aber nicht gelöscht werden.
- Beim Bearbeiten kann das Bild per Upload oder generierter Vorschau ersetzt werden.
- Ein generiertes Vorschaubild kann vor dem Speichern gelöscht werden.
- Ein gespeichertes Avatar-Bild kann nicht einzeln gelöscht werden, weil ein Avatar immer ein Bild haben muss.
- Mitgelieferte Avatare können auf den initialen Stand zurückgesetzt werden, wenn lokale Overrides existieren.
- Das Zurücksetzen wird in der Bildaktionsleiste angeboten, bestätigt und wechselt nicht das Options-Panel.
**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Bildverwendung
**Typ:** Randbedingung  
**Beschreibung:** Das System muss Avatar-Bilder auf die Avatar-Verwaltung begrenzen.  
**Akzeptanzkriterien:**
- Avatar-Bilder dienen der Darstellung und Bearbeitung in der Web-GUI.
- Avatar-Bilder werden nicht als Referenz für spätere Szenen- oder NPC-Bildgenerierung verwendet.
