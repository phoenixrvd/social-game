# Social Game

## Projektbeschreibung

Dieses Projekt ist ein experimentelles Social-Interaction-Game, bei dem der Spieler mit KI-gesteuerten Charakteren (NPCs) dialogbasierte Interaktionen führt. Ziel ist es, möglichst natürliche Gespräche zu simulieren, bei denen Emotionen, Kontext und zwischenmenschliche Dynamiken über längere Zeiträume hinweg konsistent bleiben.

Die NPCs besitzen interne Zustände (z. B. Emotionen, Vertrauen, Interesse oder aktuelle Stimmung), die sich während eines Dialogs dynamisch verändern können. Auf Basis dieser Zustände werden sowohl die Antworten der NPCs als auch visuelle Darstellungen der Szene generiert. Dadurch entsteht eine interaktive Simulation sozialer Situationen.

Neben dem Dialogsystem werden auch Bilder und optional Videos erzeugt, um Charaktere, Orte und emotionale Situationen visuell darzustellen. Die generierten Bilder orientieren sich dabei am aktuellen Zustand der Szene sowie am emotionalen Kontext der Konversation.

## Projektziele

- Realistische soziale Interaktionen zwischen Spieler und KI-Charakteren simulieren
- Emotionen, Beziehungen und Dialogdynamiken über längere Gespräche konsistent modellieren
- Mehrere spezialisierte KI-Modelle (Dialog, Sentiment, State, Bild, Video) in einer modularen Architektur kombinieren
- Grundlage für KI-basierte Social-Simulationen, Story-Games und Trainingssysteme schaffen

## KI-Modelle

Die folgende Liste enthält getestete KI-Modelle, die anhand verschiedener Kriterien geprüft und miteinander verglichen wurden. In diesem Dokument gehe ich bewusst nicht auf detaillierte Vergleichsergebnisse ein, um schneller zu einem MVP zu gelangen.

Es werden jedoch einige Schwerpunkte genannt, bei denen aktuelle Systeme an ihre Grenzen kommen und eventuell mit anderen bzw. mit nicht zensierten (NSFW) Modellen besser performen könnten.

Zum aktuellen Zeitpunkt nutze ich hauptsächlich die OpenAI-Modelle sowie Copilot-Modelle, da ich bereits entsprechende Subscriptions besitze und keine Zeit mit eigenem Hosting oder der Integration von Drittanbietern verlieren möchte.

### GPT-5.4
- Wird als Dialog-Engine genutzt, da das Modell sehr gut auf Kontext achtet und Intonation sowie Emotionen über längere Dialoge hinweg relativ gut interpolieren kann.

### GPT-5-nano
- Ein sehr performantes und kleines Modell, das für die Generierung von Zwischenprompts sowie für die Verwaltung von Long-Term- und Short-Term-Memory genutzt wird.
- Wird für Sentiment-Analysen verwendet, indem das vorherige NPC-State mit den neuen States aus dem Dialog verglichen wird. Dadurch können die Emotionen des NPC aktualisiert werden.
- Wird außerdem als „Check-System“ genutzt, um zu erkennen, ob sich der Zustand bzw. der Dialogverlauf drastisch emotional verändert hat oder ob sich die Location geändert hat.

### gpt-image-1.5
- Ist ausreichend performant und ziemlich genau.
- Kann sehr gut mit normalen Prompts umgehen, sodass keine stark technischen Prompts wie bei Stable Diffusion benötigt werden.
- Kann Umgebung und Charakter sehr gut kombinieren und dadurch Bilder generieren, die sowohl den Charakter als auch die Umgebung zeigen.
- Interpoliert Emotionen zuverlässig und passt Gesichtsausdrücke der Charaktere an die aktuelle Stimmung an.
- Wird für das initiale Charakterbild sowie für Bilder von Locations verwendet.

### Seedream-5.0
- Ein NSFW-Image-Modell.
- Benötigt relativ technische Prompts und meist ein Referenzbild, um den Charakter konsistent zu halten.
- Im Vergleich zu gpt-image-1.5 sehr teuer und wird daher nur eingesetzt, wenn **gpt-image-1.5** an seine Grenzen stößt (z. B. bei anstößigen oder grenzwertigen Szenen).
- Das Modell ist deutlich besser als Stable Diffusion, da die Prompts weniger technisch sein müssen. Das ist wichtig, weil die Bildprompts in diesem Projekt automatisch aus dem Kontext durch KI generiert werden.

### Wan-2.5
- Wird für Video-Generierung aus einem Szenenbild verwendet.
- Aktuell ein „Nice-to-have“-Feature, um Umgebungen zu animieren, falls das Projekt weit genug fortschreitet.
- Wan 2.6 ist besser, aber derzeit deutlich teurer.
- In meinen Tests liefert das Modell aktuell bessere Ergebnisse als die OpenAI-Video-Modelle.
- Bei Image-to-Video-Modellen muss darauf geachtet werden, dass sie auch NSFW-Inhalte verarbeiten können.  
  In diesem Projekt werden solche Inhalte bereits beim Image-Generator teilweise vorgefiltert. Wenn ein stärker zensiertes Modell verwendet wird, kann es passieren, dass Videos häufiger blockiert werden. Das führt zu Performance- und Kostenproblemen.