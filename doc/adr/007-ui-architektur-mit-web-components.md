---
state: defined
---

# ADR-007: UI-Architektur mit Web Components

## Status
defined

## Kontext
- Die Web-GUI benötigt eine modulare Struktur für Chat, Nachrichten, Eingabe und Szenenbild.
- Die UI-Kommunikation soll zur bestehenden ereignisorientierten Orchestrierung passen.
- Zusätzliche Framework-Abhängigkeiten sollen bewusst vermieden werden, um Komplexität und Wartungsaufwand gering zu halten.
- Inhalte aus LLM- und Backend-Antworten können HTML enthalten und sind vor dem Rendering als potenziell unsicher zu behandeln.
- Für Styling und Layout soll die Lösung projektangemessen leichtgewichtig bleiben.

## Entscheidung
- Die UI wird mit nativen Web Components umgesetzt.
- Die Komponentenkommunikation erfolgt ereignisbasiert über `CustomEvents`.
- Die Komponenten sind entlang fachlicher Verantwortungen geschnitten (`sg-chat`, `sg-message`, `sg-input`, `sg-scene-image`).
- Parent-Komponenten greifen nicht auf internes Child-DOM zu; Integration erfolgt ausschließlich über öffentliche APIs (Properties/Methoden) und `CustomEvents`.
- HTML aus LLM/Backend wird clientseitig vor dem Rendering sanitisiert.
- `sg-chat` nutzt bewusst Full-Rerender bei Zustandsänderungen.
- Es wird kein CSS-Framework eingesetzt.

## Begründung
- Browser-Standards reduzieren externe Abhängigkeiten und technische Kopplung.
- Klare Kapselung pro UI-Baustein verbessert Wartbarkeit und Erweiterbarkeit.
- Der ereignisbasierte Austausch passt zur bestehenden Orchestrierungslogik.
- Die Lösung bleibt leichtgewichtig und vermeidet zusätzlichen Build- und Laufzeit-Overhead durch ein UI-Framework.
- Öffentliche Schnittstellen statt DOM-Interna reduzieren fragile Kopplung zwischen Parent- und Child-Komponenten.
- Clientseitige Sanitization reduziert XSS-Risiken auch dann, wenn HTML aus LLM-Antworten ungefiltert geliefert wird.
- Full-Rerender im Chat hält die Implementierung einfach und nachvollziehbar.
- Bootstrap ist für den Projektumfang zu groß und bringt viele ungenutzte Komponenten mit.
- Tailwind-Utilities bieten gegenüber normalem CSS für den aktuellen Umfang keinen nennenswerten Vorteil.
- Lange Utility-Listen in Markup verschlechtern die Lesbarkeit und erschweren Reviews.
- Utility-first-Ansätze erhöhen die Kopplung von Struktur und Styling.
- Wiederverwendung über konsistente, semantische Stilbausteine wird mit Utility-Klassen weniger klar.

## Alternativen
### Alternative 1
- UI-Frameworks (React/Vue).
- Verworfen, weil zusätzliche Laufzeitabhängigkeiten, ein größeres Framework-Ökosystem und höhere Build-/Laufzeitkomplexität für den aktuellen Projektumfang keinen ausreichenden Mehrwert liefern.

### Alternative 2
- Plain JavaScript ohne komponentenbasierte Struktur.
- Verworfen, weil klare Kapselung und skalierbare Wartbarkeit bei wachsender UI fehlen.

### Alternative 3
- CSS-Framework (Bootstrap oder Tailwind).
- Verworfen, weil Bootstrap für den Projektumfang überdimensioniert ist und viele ungenutzte Komponenten mitliefert, während Tailwind gegenüber normalem CSS hier keinen nennenswerten Vorteil bietet und durch Utility-Listen Lesbarkeit, Entkopplung und Wiederverwendungslogik verschlechtert.

## Konsequenzen
- positiv: Hohe Kontrolle über Rendering und Verhalten der UI-Komponenten.
- positiv: Gute Integration mit bestehender Backend-Logik und Orchestrierung.
- positiv: Klare API-Grenzen zwischen Komponenten verbessern Wartbarkeit und Austauschbarkeit.
- positiv: Zusätzliche Sicherheitsschicht beim Rendern von HTML-Inhalten.
- positiv: Styling bleibt ohne zusätzliches CSS-Framework transparent und gezielt steuerbar.
- negativ: Kein fertiges State-Management wie in etablierten Frameworks.
- negativ: Mehr manuelle DOM- und Event-Logik in der Implementierung.
- negativ: Full-Rerender kann bei sehr langen Chat-Verläufen zu unnötigen Re-Render-Kosten führen.
- negativ: UI-Styling-Konventionen müssen ohne Framework-Defaults diszipliniert gepflegt werden.
- offen: Verbindliche Konventionen für Event-Namen und Payload-Strukturen müssen projekteinheitlich gepflegt werden.

## Annahmen
- Die Zielumgebung unterstützt Web Components und `CustomEvents` zuverlässig.
- Die modulare Aufteilung in Chat, Nachrichten, Eingabe und Szenenbild bleibt fachlich stabil.

## Offene Fragen
- Keine

## Referenzen
- `doc/requirements/sg-011-web-gui.md`
- `doc/adr/003-synchroner-update-orchestrator.md`
