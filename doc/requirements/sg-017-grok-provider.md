---
state: abgelehnt
---

# SG-017: Grok-Provider verworfen

## Kontext
SG-017 ist abgelehnt; die fachlichen Funktionen für Text- und Bildanfragen bleiben in `doc/requirements/sg-001-dialogbasierte-interaktionen.md` und `doc/requirements/sg-005-npc-bilder.md` geregelt.
Aktuell werden `MODEL_LLM_BIG=gpt-5.4`, `MODEL_LLM_SMALL=gpt-5.4-mini` und `MODEL_IMAGE=gpt-image-1.5` verwendet.

## Annahmen
- Keine

## Offene Fragen
- Keine

## Anforderungen

### Grok-Provider-Anforderungen verworfen
**Typ:** Randbedingung  
**Beschreibung:** Die Grok-Provider-Anforderungen aus SG-017 sind verworfen.  
**Akzeptanzkriterien:**
- SG-017 ist mit `state: abgelehnt` gekennzeichnet.
- Eine Grok-Provider-Unterstützung ist in SG-017 nicht als Projektanforderung festgelegt.
- Die Bildgenerierung mit Grok ist in diesem Projekt nicht lauffaehig, da im verwendeten OpenAI-kompatiblen Pfad kein `images.edit`-Aequivalent fuer Grok zur Verfuegung steht.

**Referenzen:** `doc/requirements/sg-001-dialogbasierte-interaktionen.md`, `doc/requirements/sg-005-npc-bilder.md`

### Keine LiteLLM-Implementierung in diesem Projekt
**Typ:** Randbedingung  
**Beschreibung:** Dieses Projekt muss keine LiteLLM-Implementierung enthalten.  
**Akzeptanzkriterien:**
- LiteLLM ist in SG-017 nicht als Bestandteil dieses Projekts festgelegt.
- Eine Umsetzung von Grok über LiteLLM ist in diesem Projekt nicht gefordert.

**Referenzen:** Keine

### LiteLLM für alternative Modellanbieter zulässig
**Typ:** Randbedingung  
**Beschreibung:** LiteLLM kann für alternative Modellanbieter genutzt werden.  
**Akzeptanzkriterien:**
- LiteLLM ist nicht auf Grok festgelegt.
- Die Nutzung von LiteLLM für alternative Modellanbieter bleibt zulässig.

**Referenzen:** Keine
