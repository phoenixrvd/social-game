---
state: implemented
---

# SG-003: Short-Term-Memory

## Kontext
Das System nutzt ein Kurzzeitgedächtnis für den aktuellen Gesprächs- und Handlungskontext.  
Der fachliche Fokus liegt auf der unmittelbaren Situationsverarbeitung.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Kurzfristiger Kontextbezug
**Typ:** Funktional  
**Beschreibung:** Das System muss aktuelle Informationen für die laufende Interaktion vorhalten.  
**Akzeptanzkriterien:**
- Antworten berücksichtigen den jüngsten Gesprächsverlauf.
- Der direkte Situationsbezug bleibt innerhalb einer aktiven Interaktion erhalten.

**Referenzen:** Keine

### Zeitnahe Aktualität
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss das Short-Term-Memory zeitnah an neue Interaktionen anpassen.  
**Akzeptanzkriterien:**
- Neue Eingaben beeinflussen den kurzfristigen Kontext ohne spürbare Verzögerung.
- Veraltete Kurzzeitinhalte dominieren die aktuelle Antwort nicht.

**Referenzen:** Keine

### Begrenzung auf kurzfristige Inhalte
**Typ:** Randbedingung  
**Beschreibung:** Das System muss das Short-Term-Memory auf kurzfristig relevante Inhalte beschränken.  
**Akzeptanzkriterien:**
- Langfristige Wissensinhalte werden nicht ausschließlich im Short-Term-Memory geführt.
- Der Fokus bleibt auf der aktuellen Szene und dem unmittelbaren Dialog.

**Referenzen:** Keine

