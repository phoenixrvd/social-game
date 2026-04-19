---
state: implemented
---

# SG-001: Dialogbasierte Interaktionen

## Kontext
Das System unterstützt dialogbasierte Interaktionen.  
Der fachliche Fokus liegt auf dem Austausch zwischen Nutzer und Spielwelt.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Durchführung von Dialogen
**Typ:** Funktional  
**Beschreibung:** Das System muss Dialoge zwischen Nutzer und Charakteren ermöglichen.  
**Akzeptanzkriterien:**
- Eine Nutzereingabe führt zu einer inhaltlich passenden Dialogantwort.
- Mehrere Dialogbeiträge können in einer laufenden Unterhaltung verarbeitet werden.

**Referenzen:** Keine

### Nachvollziehbare Dialogabfolge
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss die Reihenfolge von Dialogbeiträgen konsistent halten.  
**Akzeptanzkriterien:**
- Dialogbeiträge werden in der Reihenfolge ihres Eingangs verarbeitet.
- Antworten beziehen sich auf den aktuellen Stand der Unterhaltung.

**Referenzen:** Keine

### Gültiger Dialogkontext
**Typ:** Randbedingung  
**Beschreibung:** Das System muss Dialoge nur im Rahmen des definierten Spielkontexts verarbeiten.  
**Akzeptanzkriterien:**
- Antworten bleiben innerhalb der vorgesehenen Rolle und Spielsituation.
- Kontextfremde Ausgaben werden vermieden.

**Referenzen:** Keine

### Dialoggetriggerte Hintergrundverarbeitung
**Typ:** Randbedingung  
**Beschreibung:** Das System muss fachliche Hintergrundverarbeitung nur als Folge einer neuen Dialognachricht anstoßen.  
**Akzeptanzkriterien:**
- Ohne neue Dialognachricht wird keine fachliche Hintergrundfortschreibung gestartet.
- Die fachliche Hintergrundverarbeitung wird nicht allein durch periodische Scheduler-Zyklen ausgelöst.

**Referenzen:** `doc/requirements/sg-008-update-orchesrator-for-state-scene-etm-image.md`

