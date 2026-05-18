---
state: implemented
---

# SG-010: Anwendungslogging

## Kontext
Das System nutzt ein zentrales Anwendungslogging für technische Laufzeitereignisse.
Die fachliche Nachvollziehbarkeit erfolgt weiterhin primär über persistierte Laufzeitdaten, Tests und sichtbare Side-Effects.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Zentrales Anwendungslogging
**Typ:** Funktional  
**Beschreibung:** Das System protokolliert technische Laufzeitereignisse über ein zentrales Anwendungslogging.
**Akzeptanzkriterien:**
- Scheduler-Aktivitäten wie das Vormerken, Starten und Abschließen von Hintergrundjobs werden geloggt.
- Technische Ereignisse aus Services und Tools, z. B. Checkpoint-Operationen oder übersprungene Hintergrundjobs, können geloggt werden.
- Provider- oder Integrationsfehler können mit technischen Details im zentralen Anwendungslogging erscheinen, ohne die user-sichtbare Fehlermeldung zu ersetzen.
- Das Anwendungslogging erfordert keine Logger-Injektion in Services oder Tools.
- Das System konfiguriert keine eigenen dateibasierten Provider-Diagnose-Logs im Laufzeitdatenbereich.

**Referenzen:** Keine
