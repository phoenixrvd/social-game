---
state: implemented
---

# SG-011: Browserbasierte GUI für Chat und Session-Kontext

Das System stellt zusätzlich zur Verwaltungs-CLI eine browserbasierte GUI bereit, damit Spieler NPC, Szene, Dialogverlauf und Charakterbild ohne Terminal nutzen können.

## Zielbild

- Die GUI läuft als FastAPI-Webanwendung.
- Das Frontend wird als statische Single-Page-Oberfläche mit Vanilla JavaScript umgesetzt.
- Dialoge finden in der implementierten Lösung ausschließlich in dieser GUI statt.
- Die GUI nutzt denselben Session-, Store- und Persistenz-Stack wie die übrige Anwendung.

## Funktionsumfang

### Startansicht

- Beim Öffnen der GUI wird der aktuelle Session-Kontext geladen.
- Beim ersten Aufruf ohne gespeicherte GUI-Einstellungen startet die Ansicht im dunklen Theme.
- Die Ansicht zeigt mindestens:
  - auswählbaren NPC,
  - auswählbare Szene,
  - den bisherigen Chatverlauf,
  - das aktuelle NPC-Bild.
- Falls noch kein Laufzeitbild existiert, wird das Referenzbild des NPC angezeigt.
- Beim initialen Laden werden vorhandene Nachrichten schrittweise in die Ansicht übernommen, damit der Dialogverlauf direkt bis zum Ende sichtbar bleibt.
- Das zuletzt gewählte Theme wird clientseitig gespeichert und bei einem erneuten Aufruf der GUI automatisch wiederhergestellt.

### Session-Steuerung

- NPC und Szene sind direkt in der GUI umschaltbar.
- Die Auswahl für NPC und Szene liegt in einem ausklappbaren Panel unterhalb des Eingabefelds.
- Das Panel ist initial ausgeblendet und wird über einen Toggle-Button in der Aktionsleiste geöffnet oder geschlossen.
- Der visuelle Zustand des Toggle-Buttons zeigt an, ob das Panel geöffnet ist.
- Der zuletzt gewählte Panel-Zustand bleibt bei einem Seiten-Reload erhalten.
- In der Aktionsleiste steht ein zusätzlicher Button zum Umschalten zwischen hellem und dunklem Theme zur Verfügung.
- Das Icon des Theme-Buttons wechselt abhängig vom aktuell aktiven Theme.
- Der zuletzt gewählte Theme-Zustand bleibt bei einem Seiten-Reload erhalten.
- Die Auswahl wird in `.data/session.yaml` gespeichert.
- Nach einem Wechsel werden Chatverlauf, Bild und Szene für den neuen Kontext neu geladen.
- In der Chatsteuerung stehen die Aktionen Theme-Umschaltung, `Bild aktualisieren` und `Löschen` als nebeneinanderliegende Buttons zur Verfügung.
- `Löschen` fragt vor der Ausführung eine bestätigende Nutzeraktion ab.
- Nach erfolgreichem Löschen der NPC-Laufzeitdaten werden Chatverlauf und Bild für den aktiven Session-Kontext neu geladen.
- Beim Klick auf `Bild aktualisieren` wird serverseitig zuerst `emit_update` und direkt danach `schedule` für den aktiven NPC ausgelöst.

### Darstellung

- Die GUI unterstützt ein helles und ein dunkles Theme.
- Beide Themes werden vollständig clientseitig angewendet und benötigen keine serverseitige Session-Änderung.
- Das Theme beeinflusst mindestens Hintergrundflächen, Eingabebereich, Nachrichten-Bubbles, Overlays und Icon-Buttons konsistent.

### Chat-Interaktion

- Nachrichten können über ein Texteingabefeld abgeschickt werden.
- `Enter` sendet die Nachricht.
- `Shift+Enter` fügt eine neue Zeile ein.
- Der Hinweis `Enter = senden, Shift+Enter = neue Zeile` ist auf mobilen Viewports ausgeblendet.
- Während der Antworterzeugung wird in der aktiven Antwort-Bubble eine laufende Drei-Punkte-Animation angezeigt.
- Die NPC-Antwort wird token- bzw. chunkweise in die GUI gestreamt.
- Neue Spieler- und NPC-Nachrichten werden im Short-Term-Memory persistiert.

### Bilddarstellung

- Die GUI zeigt das aktuell gültige Bild des NPC in einer separaten Bildfläche.
- Bildwechsel werden ohne manuelles Browser-Refresh sichtbar.
- Die GUI prüft das aktuelle NPC-Bild asynchron im Hintergrund und aktualisiert die Darstellung bei Änderungen.
- Während ein manuell ausgelöstes Bild-Update läuft, blinkt der Button `Bild aktualisieren` transparent und beendet die Animation sofort nach Eintreffen der API-Antwort.
- Das über `GET /api/image/current` ausgelieferte Bild darf **250 KB nicht überschreiten**.
- Die Auslieferung erfolgt im WebP-Format, um eine optimale Komprimierung bei akzeptabler Qualität zu erreichen.

### Fehlerverhalten

- Wenn das Backend nicht erreichbar ist, zeigt die GUI einen klaren Hinweis.
- Wenn eine Anfrage fachlich ungültig ist (z. B. unbekannter NPC), liefert die API eine verständliche Fehlermeldung.
- Wenn das Löschen der NPC-Laufzeitdaten fehlschlägt, zeigt die GUI eine verständliche Fehlermeldung und behält den bisherigen Zustand bei.
- Alle Fehlerantworten der API folgen **RFC 7807 – Problem Details for HTTP APIs** mit `Content-Type: application/problem+json` und den Pflichtfeldern `type`, `status` und `detail`.

## API-Vertrag

Die FastAPI-Anwendung stellt mindestens folgende Endpunkte bereit:

- `GET /` liefert die GUI aus.
- `GET /favicon.ico` liefert das Standard-Favicon für den Browser-Tab.
- `GET /icons/{file_path}` liefert statische App-Icons (z. B. PNG/Apple-Touch).
- `GET /api/state` liefert den initialen GUI-Zustand.
- `PUT /api/session` aktualisiert NPC und/oder Szene im Session-Kontext.
- `DELETE /api/npc/reset-active` löscht das Laufzeitverzeichnis des aktiven Session-NPC unter `.data/npcs/<npc_id>` und liefert den aktualisierten GUI-Zustand.
- `POST /api/chat/stream` streamt die NPC-Antwort inkrementell für die GUI.
- `GET /api/image/current` liefert das aktuell gültige NPC-Bild für den aktiven Session-Kontext.
- `HEAD /api/image/current` liefert Metadaten für asynchrone Bildaktualisierung ohne vollständigen Bilddownload.
- `POST /api/image/refresh-active` stößt ein sofortiges Bild-Update für den aktiven NPC an und führt intern `emit_update` vor `schedule` aus.

## Betriebsverhalten

- Der Standardstart erfolgt über `sg web`.
- Beim Start der Web-GUI werden die Watcher für `ltm`, `scene`, `state` und `image` automatisch im Hintergrund mitgestartet.
- Dadurch können sich Szene, Zustand, Long-Term-Memory und Bild auch außerhalb eines gerade laufenden Requests weiterentwickeln.

## Akzeptanzkriterien

- Die GUI ist lokal im Browser nutzbar.
- GUI und CLI verwenden denselben persistierten Session-Kontext.
- Die GUI zeigt beim Laden vorhandene STM-Nachrichten an und scrollt den sichtbaren Dialog an das Ende.
- Die GUI startet ohne gespeicherte Theme-Auswahl standardmäßig im dunklen Theme.
- Nach einem Theme-Wechsel zeigt der Theme-Button ein zum Zustand passendes Icon und der gewählte Zustand bleibt nach einem Seiten-Reload erhalten.
- Nach dem Senden einer Nachricht erscheint die NPC-Antwort gestreamt in der GUI und ist anschließend im STM sichtbar.
- Ein NPC-/Szenenwechsel in der GUI aktualisiert die Ansicht ohne weiteres Terminalkommando.
- Das Löschen der aktiven NPC-Laufzeitdaten ist nur nach Bestätigung möglich und setzt die Ansicht auf den Initialzustand (inkl. neu geladenem Chatverlauf und Bild) zurück.
- Das aktuell gültige NPC-Bild ist über die GUI sichtbar und aktualisiert sich auch bei watchergetriebenen Änderungen asynchron.
- Beim manuellen Bild-Refresh blinkt der Button `Bild aktualisieren` transparent und stoppt die Animation unmittelbar nach der API-Antwort.
- Das über `GET /api/image/current` ausgelieferte Bild ist kleiner als 250 KB und wird als WebP ausgeliefert.
- Alle API-Fehlerantworten haben den Content-Type `application/problem+json` und enthalten die Felder `type`, `status` und `detail` gemäß RFC 7807.
