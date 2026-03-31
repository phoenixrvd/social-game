---
state: implemented
---

# SG-007: Zweistufige Bildgenerierung

Die Bildgenerierung verwendet einen 2-stufigen Prozess.
Der aktuell erzeugte Gesamtprompt ist sehr lang, stark aus Text-Kontext aufgebaut und wird daher vor der Bildgenerierung für das Bildmodell optimiert.
Das Bildmodell erhält das Referenzbild direkt und ist dafür gebaut, visuelle Kontinuität selbst zu steuern – eine vorgeschaltete Bildanalyse ist daher nicht notwendig.

## Technische Details

- SG-007 erweitert den Bild-Workflow aus [SG-005](sg-005-npc-bilder.md).
- Der aus NPC-, State-, Scene-, STM- und LTM-Daten zusammengesetzte Prompt dient als fachliche Rohquelle.
- Dieser Rohprompt wird nicht direkt an das Bildmodell geschickt.

### Stufe 1: Rohprompt für das Bildmodell optimieren

- Der Rohprompt wird aus NPC-, State-, Szene-, STM- und LTM-Daten aufgebaut und an ein Text-LLM übergeben.
- Ziel ist ein kürzerer, bildmodell-tauglicher Prompt mit Fokus auf:
  - stabile Identitätsmerkmale des Charakters,
  - aktuell relevante sichtbare Veränderungen,
  - Stimmung, Szene, Licht und Kleidung,
  - klare visuelle Prioritäten,
  - möglichst wenig unnötigen Erklärtext.
- Die Ausgabe dieser Stufe ist ein optimierter Bildprompt, der in natürlicher Sprache für ein Bildmodell formuliert ist.
- Für diese Stufe wird der Prompt `prompts/image_build_prompt.md` verwendet.

### Stufe 2: Bildveränderung mit Referenzbild und optimiertem Prompt

- Das Bildmodell erhält:
  1. das aktuelle Referenzbild,
  2. den zuletzt freigegebenen optimierten Prompt.
- Als Referenzbild gilt das derzeit aktuelle Charakterbild gemäß SG-005 (also bevorzugt das vorhandene `.data`-Bild, sonst das statische NPC-Referenzbild).
- Die Bildgenerierung erfolgt weiterhin als Edit des Referenzbildes, nicht als völlig neue Generierung ohne Bildbezug.
- Das Bildmodell steuert visuelle Kontinuität (Gesicht, Körperbau, Haarfarbe etc.) selbst anhand des Referenzbildes.
- Ausgabeformat und Persistenzverhalten aus SG-005 bleiben erhalten:
  - `png`
  - `moderation=low`
  - `orientation=portrait`
  - `size=1024x1536`
  - Persistenz nach `.data/npcs/<npc_id>/<scene_id>/img.png`
  - Backup eines vorhandenen Datenbildes nach `.data/npcs/<npc_id>/<scene_id>/img_backup/` vor dem Überschreiben

### Ausführung und Auslöser

- Die beiden Stufen werden heute intern durch den `ImageUpdater` orchestriert.
- Auslöser ist ein Run-Trigger aus `SceneUpdater` oder `StateUpdater`; ohne Trigger läuft `ImageUpdater.schedule()` als No-Op.
- Für Kosteneffizienz wird nach Prompt-Optimierung zusätzlich geprüft, ob der neue Prompt relevant vom vorherigen Prompt abweicht (exakt, Fuzzy-Ähnlichkeit, Token-Überlappung). Bei zu hoher Ähnlichkeit wird die Bildgenerierung übersprungen.
- Manueller Refresh über die Web-API (`/api/image/refresh-active`) setzt den Trigger und ruft `schedule(force=True)` auf; dabei werden die Ähnlichkeits-Skips bewusst übergangen.
- Der globale Session-Kontext (`sg session set`) bestimmt weiterhin, für welchen NPC und welche Szene der Bildworkflow läuft.
- Ein manuelles Zurücksetzen des aktuellen Datenbilds bleibt über `sg image-revert` möglich.

### Modellstrategie

- Für Stufe 1 wird ein Text-LLM verwendet.
- Für Stufe 2 wird das Bildmodell verwendet.
- Die verwendeten Modelle sollen per `.env` konfigurierbar bleiben, analog zur bestehenden Modellstrategie aus [ADR-004](../adr/004-modellstrategie.md).

## Akzeptanzkriterien

- Der Rohprompt wird nicht direkt an das Bildmodell übergeben.
- Der optimierte Prompt wird persistent gespeichert und beim nächsten Lauf als Vergleichsstand verwendet.
- Der `ImageUpdater` verwendet den optimierten Prompt zusammen mit dem Referenzbild für die Bildaktualisierung.
- Backup- und Persistenzlogik aus SG-005 bleiben erhalten.
- Eine Bildaktualisierung läuft nur, wenn zuvor `SceneUpdater` oder `StateUpdater` einen Run-Trigger gesetzt hat.
- Eine Bildaktualisierung wird übersprungen, wenn der neue Prompt dem letzten Prompt zu ähnlich ist.
