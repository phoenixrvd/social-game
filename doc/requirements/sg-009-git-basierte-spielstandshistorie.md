---
state: implemented
---

# SG-009: Git-basierte Spielstandshistorie

## Kontext
Das System soll Spielstände der aktiven Sitzung als nachvollziehbare Historie verwalten.  
Die Historie umfasst Speicherung, Wiederherstellung und die zugehörige Bedienung in der Web-GUI für den Laufzeitdatenbestand unter `.data/<npc>`.

## Annahmen
- Die Auswahl des kleinen LLM-Modells ist nicht Teil dieser Anforderung.

## Offene Fragen
- Keine

## Anforderungen

### Git-basierte Speicherung von Spielständen
**Typ:** Funktional  
**Beschreibung:** Das System muss Spielstände der aktiven Sitzung als Git-Checkpoints speichern.  
**Akzeptanzkriterien:**
- Ein manueller Speichervorgang erzeugt einen neuen Checkpoint in Git.
- Ein gespeicherter Checkpoint ist als wiederherstellbarer Spielstand verfügbar.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Geltungsbereich der Spielstandsspeicherung
**Typ:** Randbedingung  
**Beschreibung:** Das System muss bei jedem Checkpoint den vollständigen Laufzeitdatenbestand des aktiven NPC unter `.data/<npc>` berücksichtigen.  
**Akzeptanzkriterien:**
- Ein Checkpoint umfasst alle Inhalte unter `.data/<npc>`.
- Inhalte außerhalb von `.data/<npc>` sind nicht Teil des Checkpoints.

**Referenzen:** Keine

### Commit-Nachricht für Checkpoints
**Typ:** Randbedingung  
**Beschreibung:** Das System muss für Checkpoints ein einheitliches Commit-Nachrichtenformat mit automatisch abgeleiteter Kurzfassung verwenden.  
**Akzeptanzkriterien:**
- Die Commit-Nachricht eines Checkpoints besteht nur aus einer Kurzfassung (max 10 Wörter).
- NPC-ID und Scene-ID sind nicht Teil der Commit-Nachricht.
- Die Kurzfassung wird aus dem letzten Turn abgeleitet.
- Für die Ableitung der Kurzfassung wird ein kleines LLM-Modell verwendet.
- Die Kurzfassung enthält höchstens 10 Wörter.

**Referenzen:** Keine

### Wiederherstellung gespeicherter Spielstände
**Typ:** Funktional  
**Beschreibung:** Das System muss gespeicherte Spielstände als Ziel einer Wiederherstellung auswählbar machen.  
**Akzeptanzkriterien:**
- Ein gespeicherter Checkpoint kann als Ziel einer Wiederherstellung ausgewählt werden.
- Nach erfolgreicher Wiederherstellung entspricht der aktive Spielstand dem ausgewählten Checkpoint.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Sicherung vor Wiederherstellung bei Änderungen
**Typ:** Funktional  
**Beschreibung:** Das System muss vor der Wiederherstellung eines älteren Spielstands vorhandene Änderungen absichern.  
**Akzeptanzkriterien:**
- Wenn vor der Wiederherstellung Änderungen im aktuellen `.data/<npc>`-Stand vorliegen, wird zuerst ein normaler Checkpoint erzeugt.
- Die Wiederherstellung wird erst nach erfolgreicher Sicherung fortgesetzt.

**Referenzen:** Keine

### Revert-Commit bei Wiederherstellung
**Typ:** Funktional  
**Beschreibung:** Das System muss jede Wiederherstellung eines älteren Spielstands als Revert-Commit dokumentieren.  
**Akzeptanzkriterien:**
- Die Wiederherstellung eines älteren Spielstands erzeugt einen neuen Commit.
- Die Commit-Nachricht beginnt mit `[revert to]`.
- Die Commit-Nachricht enthält die Uhrzeit des Ziel-Commits.
- Die Commit-Nachricht enthält das Datum des Ziel-Commits.
- Die Commit-Nachricht enthält die Message des Ziel-Commits.
- Die Commit-Nachricht enthält keine Commit-ID des Ziel-Commits.
- Der neue Commit stellt den Zustand des Ziel-Commits als aktiven Spielstand her.

**Referenzen:** Keine

### Löschung von Checkpoints bei Verlauf-Löschen
**Typ:** Funktional  
**Beschreibung:** Das System muss beim Löschen des Verlaufs die Checkpoints des betroffenen `.data/<npc>`-Bereichs mit löschen.  
**Akzeptanzkriterien:**
- Nach Ausführung von `Verlauf löschen` sind für den betroffenen `.data/<npc>`-Bereich keine Checkpoints mehr verfügbar.

**Referenzen:** Keine

### History-Panel im Eingabebereich
**Typ:** Funktional  
**Beschreibung:** Das System muss in `sg-input` ein History-Panel für Spielstände bereitstellen.  
**Akzeptanzkriterien:**
- In `sg-input` ist ein History-Panel vorhanden.
- Unter der History-Liste ist ein Button `Zwischenstand speichern` vorhanden.
- Das Auslösen des Buttons startet den manuellen Speichervorgang für einen Checkpoint.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Aktivierung des History-Panels
**Typ:** Funktional  
**Beschreibung:** Das System muss das History-Panel über ein eigenes Control mit Save-Icon aktivierbar machen.  
**Akzeptanzkriterien:**
- Für das History-Panel ist ein eigenes Control mit Save-Icon vorhanden.
- Das bestehende Bild-Control zeigt nur ein Bild-Icon.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Darstellung von History-Einträgen
**Typ:** Funktional  
**Beschreibung:** Das System muss History-Einträge mit Speicherdatum anzeigen.  
**Akzeptanzkriterien:**
- Jeder History-Eintrag zeigt seine Überschrift an.
- Neben der Überschrift wird das Datum der Speicherung angezeigt.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`

### Bestätigung und Neuladen bei Wiederherstellung
**Typ:** Funktional  
**Beschreibung:** Das System muss vor der Wiederherstellung eines History-Eintrags eine Bestätigung verlangen und danach die App neu laden.  
**Akzeptanzkriterien:**
- Ein Klick auf einen History-Eintrag öffnet vor der Wiederherstellung einen Bestätigungsdialog.
- Ohne Bestätigung bleibt der aktive Spielstand unverändert.
- Nach erfolgreicher Wiederherstellung wird die komplette App neu geladen.

**Referenzen:** `doc/requirements/sg-011-web-gui.md`
