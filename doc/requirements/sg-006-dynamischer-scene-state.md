---
state: implemented
---

# SG-006: Dynamischer Scene-State

## Kontext
Das System verwaltet einen dynamischen Zustand von Szenen.  
Der fachliche Fokus liegt auf Veränderungen innerhalb der Spielumgebung.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Aktualisierung des Szenenzustands
**Typ:** Funktional  
**Beschreibung:** Das System muss den Zustand einer Szene anhand relevanter Ereignisse aktualisieren.  
**Akzeptanzkriterien:**
- Ereignisse in der Szene führen zu nachvollziehbaren Zustandsänderungen.
- Der aktuelle Szenenzustand steht für nachfolgende Interaktionen zur Verfügung.

**Referenzen:** Keine

### Konsistenter Szenenkontext
**Typ:** Nicht-funktional  
**Beschreibung:** Das System muss den Szenenzustand widerspruchsarm führen.  
**Akzeptanzkriterien:**
- Neue Zustände widersprechen dem bisherigen Szenenverlauf nicht ohne erkennbare Ursache.
- Interaktionen beziehen sich auf denselben aktuellen Szenenzustand.

**Referenzen:** Keine

### Begrenzung auf szenenrelevante Inhalte
**Typ:** Randbedingung  
**Beschreibung:** Das System muss den Scene-State auf Inhalte der jeweiligen Szene begrenzen.  
**Akzeptanzkriterien:**
- Szenenfremde Informationen werden nicht als Teil des Scene-State behandelt.
- Der Scene-State bleibt an die aktive Szene gebunden.

**Referenzen:** Keine

