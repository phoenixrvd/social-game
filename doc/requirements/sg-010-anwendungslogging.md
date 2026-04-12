---
state: removed
---

# SG-010: Anwendungslogging (entfernt)

## Kontext
Anwendungslogging wurde aus dem System entfernt.
Die Nachvollziehbarkeit erfolgt aktuell über persistierte Laufzeitdaten, Tests und sichtbare Side-Effects.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Keine Anwendungslogs
**Typ:** Funktional  
**Beschreibung:** Das System erzeugt keine eigenen Anwendungslogs.
**Akzeptanzkriterien:**
- Es gibt kein `engine.logging`-Modul.
- Services und Updater enthalten keine Logger-Injektion.
- Die Abhängigkeit `injector` wird nicht für Logging oder Service-Aufbau genutzt.

**Referenzen:** Keine
