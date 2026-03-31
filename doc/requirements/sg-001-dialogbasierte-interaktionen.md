---
state: implemented
---

# SG-001: Dialogbasierte Interaktionen

Das System soll dialogbasierte Interaktionen zwischen einem Spieler und KI-gesteuerten Charakteren (NPCs) simulieren.

## Globaler Interaktionskontext (Ergänzung)

- Es gibt ein CLI-Kommando, mit dem NPC und Szene für die Interaktion global festgelegt werden.
- Der gesetzte Zustand wird in `.data/session.yaml` gespeichert.
- Dieser Session-Zustand wird zusammen mit der Konfiguration geladen und steht danach der Web-GUI sowie den Watchern zur Verfügung.
- Der aktuelle Interaktionskontext wird zentral aus der Session geladen.

## Technische Details

- Die Kommunikation erfolgt mit einer LLM, und Dialoge sollen über längere Zeiträume hinweg konsistent bleiben.
- Konfiguration und Einstellungen von Szenen und NPCs sollen persistierbar sein.
- Der eigentliche Dialog findet in der implementierten Lösung ausschließlich in der Web-GUI statt.
- Neue Spieler- und NPC-Nachrichten werden im Short-Term-Memory persistiert und stehen damit auch den Watchern für State-, Scene-, LTM- und Bild-Updates zur Verfügung.
- Der Turn-Kontext für die Dialog-LLM wird über einen gemeinsamen Systemprompt aufgebaut, der NPC-Rolle, Character Data, Character Description, Long-Term-Memory, aktuelle Szene und aktuellen NPC-State enthält.
- Nach dem Systemprompt folgen die STM-Nachrichten; die aktuelle User-Nachricht wird separat als letzter Turn hinzugefügt.

