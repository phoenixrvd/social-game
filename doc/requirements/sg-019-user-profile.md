---
state: implemented
---

# SG-019: User Profile

## Kontext
Das System verwaltet ein User Profile als langfristige Sicht des aktiven NPC auf den Spieler. Das Profil
enthaelt manuell hinterlegte, stabile Informationen und wird als Kontext im Dialog verwendet.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Bereitstellung und Nutzung im Dialogkontext
**Typ:** Funktional  
**Beschreibung:** Das System muss ein User Profile als optionalen Langzeitkontext ueber den Spieler im Dialogkontext bereitstellen und ueber RAG nutzen.  
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
- Das Basisprofil liegt unter `npcs/user_profile.md`.
- Lokale Overrides liegen unter `.overrides/npcs/user_profile.md`.
- Das aktive Runtime-Profil liegt unter `.data/npcs/<npc_id>/<scene_id>/user_profile.md`.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Priorisierung der Datenschichten
**Typ:** Randbedingung  
**Beschreibung:** Das System muss User Profiles über die bestehende Datei-Überladelogik mit definierter Priorität auflösen.  
**Akzeptanzkriterien:**
- `.data/npcs/<npc_id>/<scene_id>/user_profile.md` hat die höchste Priorität.
- `.overrides/npcs/user_profile.md` hat Vorrang vor `npcs/user_profile.md`.
- `npcs/user_profile.md` ist der Fallback.
- Fehlende Ebenen werden auf die jeweils nächste verfügbare Ebene zurückgeführt.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Manuelle statische Profilpflege
**Typ:** Funktional  
**Beschreibung:** Das System muss das User Profile ausschliesslich als manuell gepflegte, statische Hinterlegung fuehren.  
**Akzeptanzkriterien:**
- Profilinhalte aendern sich nur durch manuelle Bearbeitung.
- Ein Dialog allein erzeugt keinen neuen Profilinhalt.
- Ein Dialog allein veraendert keinen vorhandenen Profilinhalt.

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
**Beschreibung:** Das System muss das User Profile im Bereich „Allgemein“ der Web-GUI editierbar bereitstellen.  
**Akzeptanzkriterien:**
- Der Bereich ist sichtbar mit der Überschrift `Dein Profil`.
- Das User Profile ist über ein Textarea-Feld editierbar.
- Änderungen werden gespeichert, sobald das Feld den Fokus verliert.
- Die Speicherung erfolgt unter `.data/npcs/<npc_id>/<scene_id>/user_profile.md`.
**Referenzen:** `doc/requirements/sg-011-web-gui.md`
