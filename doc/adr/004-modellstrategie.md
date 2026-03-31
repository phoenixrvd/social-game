# ADR 004: Modellstrategie

**Status:** Akzeptiert  
**Datum:** 2026-03-15

## Kontext

Das Projekt benoetigt KI-Modelle fuer verschiedene Aufgaben mit unterschiedlichen
Anforderungen an Qualitaet, Latenz und Kosten:

- **Dialoge** brauchen Kontexttreue, emotionale Konsistenz und Streaming.
- **Hilfsaufgaben** (LTM-Zusammenfassung, State-Update) brauchen zuverlaessige
  Verarbeitung von strukturiertem Text, aber keine hohe Dialogqualitaet.
- **Bildgenerierung** braucht ein Modell, das normale Prompts versteht und
  Charakter und Umgebung konsistent kombinieren kann.

Die Modelle werden ueber `.env`-Variablen konfiguriert, damit sie ohne Code-Aenderung
ausgetauscht werden koennen.

## Entscheidung

### Dialogmodell (`MODEL_LLM_BIG`, Default: `gpt-5.4`)

- Wird fuer alle NPC-Dialoge verwendet (Streaming).
- Gewaehlt wegen guter Kontexttreue und emotionaler Konsistenz ueber laengere Dialoge.
- Dasselbe Modell wird fuer die LTM-Zusammenfassung verwendet, damit Interpretation
  und Gewichtung zwischen Dialog und Memory konsistent bleiben.

### Hilfsmodell (`MODEL_LLM_SMALL`, Default: `gpt-5-nano`)

- Model wird für automatisierung von entscheidungen genommen, wie z.B. erkennen ob die szene sich signifikant geändert wurde und das Bild neu generiert werden muss.
- Gewaehlt wegen geringer Latenz und niedrigerer Kosten gegenueber dem Dialogmodell.
- Aufgaben: strukturierten YAML-State aus Gespraechskontext ableiten.

### Bildmodell (`MODEL_LLM_IMG_BASE`, Default: `gpt-image-1.5`)

- Wird fuer die Charakterbildgenerierung verwendet.
- Gewaehlt weil es normale (nicht technische) Prompts verarbeiten kann. Wchtig, da Bildprompts automatisch durch das LLM erzeugt werden.
- Kombination von Charakter und Szenenkontext funktioniert zuverlaessig.
- Modell ist per `.env` ueberschreibbar, z. B. fuer NSFW-Szenarien mit einem weniger zensierten Modell.
- Kleineres modell wie `gpt-image-1.5` ist für testing ok (um token-Limit zu umgehen), aber nicht gut genug fuer die Qualitaet der Charakterbilder.

## Konsequenzen

- Modellwechsel erfordern keine Code-Aenderung.
- Die Trennung zwischen grossem und kleinem Modell reduziert Kosten bei Hilfsaufgaben.
- Durch die Verwendung desselben Modells fuer Dialog und LTM bleiben Memory-Eintraege
  semantisch konsistent mit dem Dialogstil.
- Bei Bedarf kann das Bildmodell pro Deployment-Szenario gewechselt werden
  (z. B. auf ein NSFW-faehiges Modell fuer entsprechende Szenen).

