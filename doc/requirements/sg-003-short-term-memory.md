---
state: implemented
---

# SG-003: Short-Term-Memory

## Kontext
Das System nutzt ein Kurzzeitgedächtnis für den aktuellen Gesprächs- und Handlungskontext.  
Der fachliche Fokus liegt auf der unmittelbaren Situationsverarbeitung.
Ältere Inhalte, die nicht mehr unmittelbar in den Prompt gehören, können als Episodic Term Memory (ETM) abrufbar bleiben.
Auch kurzfristige Inhalte werden aus Sicht des aktiven NPC interpretiert.

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
- Beim Kürzen des STM dürfen relevante ältere Gesprächsabschnitte in ETM überführt werden.
- ETM-Retrieval ersetzt nicht den direkten STM-Kontext der letzten Nachrichten.

**Referenzen:** `doc/requirements/sg-015-episodic-term-memory.md`

### NPC-Perspektive
**Typ:** Randbedingung
**Beschreibung:** Das System muss Short-Term-Memory als aktuellen Kontext des aktiven NPC behandeln.
**Akzeptanzkriterien:**
- STM erhält den aktuellen Dialogverlauf, damit der NPC seine laufende Situation versteht.
- Aus STM abgeleitete Memory-Inhalte werden aus Sicht des NPC formuliert.
- STM wird nicht als wertende externe Zusammenfassung des Chats gespeichert.

**Referenzen:** `doc/requirements/sg-001-dialogbasierte-interaktionen.md`
