---
state: implemented
---

# SG-013: Security- und Lizenzstrategie

## Kontext
Das Open-Source-Projekt befindet sich im Alpha-Status für Entwickler und dient primär dem Experimentieren. Sicherheitsmeldungen, Supportgrenzen, Haftungsausschluss und Lizenzrahmen müssen dazu konsistent beschrieben sein.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Vertrauliche Meldung von Sicherheitslücken
**Typ:** Funktional  
**Beschreibung:** Das Projekt muss für Sicherheitslücken einen vertraulichen Meldeweg bereitstellen.  
**Akzeptanzkriterien:**
- Für Sicherheitslücken ist ein nicht-öffentlicher Meldeweg benannt.
- Öffentliche Issues sind nicht als vorgesehener Meldeweg für Sicherheitslücken beschrieben.

**Referenzen:** `SECURITY.md`

### Begrenzter Support für Sicherheitskorrekturen
**Typ:** Randbedingung  
**Beschreibung:** Das Projekt muss den Support für Sicherheitskorrekturen auf den neuesten Release-Stand des `main`-Branches begrenzen.  
**Akzeptanzkriterien:**
- Als unterstützt ist nur der neueste Release-Stand des `main`-Branches beschrieben.
- Ältere Releases sind nicht als Empfänger von Sicherheitskorrekturen beschrieben.

**Referenzen:** `SECURITY.md`

### Transparente Kommunikation des experimentellen Betriebs
**Typ:** Nicht-funktional  
**Beschreibung:** Das Projekt muss seinen experimentellen Charakter und die reduzierten Betriebszusagen transparent ausweisen.  
**Akzeptanzkriterien:**
- Der Alpha-Status für Entwickler ist dokumentiert.
- Der Fokus auf Experimentieren ist dokumentiert.
- Bewusst minimales Fehlerhandling ist dokumentiert.
- Der Betrieb erfolgt "as is" bzw. auf eigenes Risiko.

**Referenzen:** `README.md`, `SECURITY.md`, `LICENSE`

### Bereitstellung unter Open-Source-Lizenz
**Typ:** Funktional  
**Beschreibung:** Das Projekt muss unter einer Open-Source-Lizenz bereitgestellt werden.  
**Akzeptanzkriterien:**
- Eine Lizenz ist im Projekt enthalten.
- Die Lizenz beschreibt Nutzung, Änderung und Weitergabe des Projekts.

**Referenzen:** `LICENSE`

### Erhalt von Lizenz- und Copyright-Hinweisen
**Typ:** Randbedingung  
**Beschreibung:** Die Lizenzstrategie muss bei Weitergabe des Projekts den Erhalt von Lizenz- und Copyright-Hinweisen verlangen.  
**Akzeptanzkriterien:**
- Die Lizenz verlangt die Beibehaltung des Copyright-Hinweises.
- Die Lizenz verlangt die Beibehaltung des Lizenzhinweises.

**Referenzen:** `LICENSE`
