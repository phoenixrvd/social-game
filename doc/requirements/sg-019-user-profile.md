---
state: implemented
---

# SG-019: User Profile

## Kontext
Das System verwaltet ein User Profile als langfristige Sicht des aktiven NPC auf die Nutzerin oder den Nutzer. Das Profil enthält manuell hinterlegte, stabile Informationen und wird als Kontext im Dialog verwendet.

## Annahmen
- Das User Profile ist an den aktiven NPC-Szenen-Kontext gebunden.
- Aktuelle Nachrichten im Short-Term-Memory haben bei Widersprüchen Vorrang vor Profilinformationen.

## Offene Fragen
- Keine

## Anforderungen

### Bereitstellung und Nutzung im Dialogkontext
**Typ:** Funktional  
**Beschreibung:** Das System muss ein User Profile als optionalen Langzeitkontext über die Nutzerin oder den Nutzer im Dialogkontext bereitstellen.  
**Akzeptanzkriterien:**
- Ein User Profile kann leer sein.
- Das System funktioniert auch ohne vorhandenes User Profile.
- Das aufgelöste User Profile kann im NPC-Dialogkontext berücksichtigt werden.
- Das User Profile kann Interpretation, Ton, Nähe und Verhalten der NPC-Antwort beeinflussen.
- Das User Profile wird nicht explizit als eigener Dialoginhalt ausgegeben.
**Referenzen:** `doc/requirements/sg-001-dialogbasierte-interaktionen.md`, `doc/requirements/sg-003-short-term-memory.md`

### Speicherorte des User Profiles
**Typ:** Randbedingung  
**Beschreibung:** Das System muss User Profiles an definierten Speicherorten unterstützen.  
**Akzeptanzkriterien:**
- Das aktive User Profile wird aus `user_profile.md` gelesen.
- Die Auflösung nutzt den aktiven Runtime-Kontext vor Override vor Default.
- Runtime-Profile liegen unter `.data/npcs/<npc_id>/<scene_id>/user_profile.md`.
- Override-Profile liegen unter `.overrides/npcs/user_profile.md`.
- Default-Profile liegen unter `npcs/user_profile.md`.
**Referenzen:** `doc/requirements/sg-016-overrides-verzeichnis.md`

### Manuelle statische Profilpflege
**Typ:** Funktional  
**Beschreibung:** Das System muss das User Profile ausschließlich als manuell gepflegte, statische Hinterlegung führen.  
**Akzeptanzkriterien:**
- Profilinhalte ändern sich nur durch explizites Speichern durch die Nutzerin oder den Nutzer.
- Ein Dialog allein erzeugt keinen neuen Profilinhalt.
- Ein Dialog allein verändert keinen vorhandenen Profilinhalt.

### Profilgröße
**Typ:** Randbedingung  
**Beschreibung:** Das User Profile ist auf eine sozial realistische und kognitiv handhabbare Größe begrenzt.  
**Akzeptanzkriterien:**
- Das User Profile enthält in der Regel maximal 25 Einträge.
- Jeder Eintrag entspricht einem stabilen, eigenständigen Fakt im Format `- schlüssel: wert`.
- Duplikate oder überholte Einträge werden bei der Fortschreibung entfernt.

### NPC-Perspektive
**Typ:** Randbedingung  
**Beschreibung:** Das System muss das User Profile aus Sicht des aktiven NPC führen.  
**Akzeptanzkriterien:**
- Inhalte beschreiben, was der aktive NPC über die Nutzerin oder den Nutzer weiß oder annimmt.
- Unsicherheiten werden als Eindruck formuliert.
- Das User Profile enthält keine externe oder systemische Analyse der Nutzerin oder des Nutzers.
- Es wird kein zusätzliches Wissen außerhalb von Profil und Dialog erfunden.
**Referenzen:** `doc/requirements/sg-003-short-term-memory.md`, `doc/requirements/sg-015-episodic-term-memory.md`

### Editierbarkeit in der Web-GUI
**Typ:** Funktional  
**Beschreibung:** Das System muss das User Profile im Bereich `Allgemein` der Web-GUI editierbar bereitstellen.  
**Akzeptanzkriterien:**
- Der Bereich enthält eine Textfläche für das User Profile.
- Änderungen werden über `Profil speichern` gespeichert.
- Die Speicherung erfolgt für den aktiven NPC-Szenen-Kontext unter `.data/npcs/<npc_id>/<scene_id>/user_profile.md`.
**Referenzen:** `doc/requirements/sg-011-web-gui.md`
