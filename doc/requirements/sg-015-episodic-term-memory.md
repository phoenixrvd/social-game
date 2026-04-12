---
state: implemented
---

# SG-015: Episodic Term Memory (ETM)

## Kontext
Das System soll sich an relevante frühere Gesprächsinhalte erinnern, auch wenn sie nicht mehr im unmittelbaren Short-Term-Memory liegen.
Episodic Term Memory (ETM) speichert deshalb ältere Gesprächsabschnitte als kompakte Episoden in einer Vector-Datenbank und stellt sie vor NPC-Antworten per semantischem Retrieval bereit.
Statische Beziehungsgrundlagen werden separat über `relationship.md` in den initialen State eingebracht.
ETM-Episoden werden aus Sicht des aktiven NPC gespeichert, nicht als bloße Chat-Beschreibung.

## Annahmen
- Die lokal eingebettete Vector-Datenbank für ETM-Retrieval ist Chroma.
- Episoden werden pro `npc_id` und `scene_id` isoliert gespeichert.
- State und Scene dürfen als Kontext für Episodenbildung und Antwortgenerierung dienen, sind aber keine primären Memory-Quellen.
- ETM ist kein direkter Bildgenerierungs-Kontext.

## Offene Fragen
- Keine

## Anforderungen

### ETM-Episodenbildung aus altem STM
**Typ:** Funktional
**Beschreibung:** Das System muss ältere Short-Term-Memory-Nachrichten in kompakte ETM-Episoden überführen.
**Akzeptanzkriterien:**
- Die neuesten STM-Nachrichten bleiben als unmittelbarer Gesprächskontext direkt im STM erhalten.
- Verarbeitete ältere STM-Nachrichten werden als zusammenhängende ETM-Gesprächsepisode zusammengefasst.
- Eine Episode enthält den fachlichen Kern des Gesprächsabschnitts, relevante Aussagen des Spielers und relevante Reaktionen des NPC.
- Kurzfristiger Smalltalk ohne späteren Erinnerungswert wird nicht als eigene Episode priorisiert.
- Eine Episode beschreibt, was der NPC erlebt, wahrnimmt oder daraus für die Beziehung ableitet.
- Eine Episode ist keine neutrale Mitschrift und keine bloße Beschreibung des Chats.

**Referenzen:** `doc/requirements/sg-003-short-term-memory.md`

### Speicherung in Chroma
**Typ:** Funktional
**Beschreibung:** Das System muss ETM-Episoden vektorisieren und pro aktiver Spielinstanz in Chroma speichern.
**Akzeptanzkriterien:**
- Jede gespeicherte Episode wird mit einem Embedding abgelegt.
- Die Speicherung erfolgt isoliert pro `npc_id` und `scene_id`.
- Episoden anderer NPCs oder Szenen werden nicht im selben Retrieval-Kontext verwendet.
- Ein Reset der aktiven Spielinstanz entfernt auch die zugehörigen Episoden.

**Referenzen:** `doc/adr/002-datenspeicherung-data-verzeichnis.md`, `doc/adr/008-chroma-als-vector-datenbank.md`

### ETM-Retrieval vor NPC-Antworten
**Typ:** Funktional
**Beschreibung:** Das System muss vor einer NPC-Antwort relevante frühere Episoden anhand der aktuellen User-Nachricht abrufen und in den Prompt aufnehmen.
**Akzeptanzkriterien:**
- Die aktuelle User-Nachricht ist die primäre Retrieval-Query.
- Das Retrieval lädt nur Episoden aus dem aktiven `npc_id`- und `scene_id`-Kontext.
- Die Anzahl abgerufener Episoden ist begrenzt und nicht als starres Verhältnis zu STM-Nachrichten definiert.
- Wenn keine relevante Episode vorhanden ist, bleibt der Prompt ohne erfundene Erinnerung.
- Der direkte STM-Kontext bleibt gegenüber Retrieval-Treffern als aktuelle Gesprächslage erkennbar.

**Referenzen:** `doc/requirements/sg-001-dialogbasierte-interaktionen.md`, `doc/requirements/sg-003-short-term-memory.md`

### ETM-Ladekontexte
**Typ:** Randbedingung
**Beschreibung:** Das System muss ETM nur in fachlich passenden Kontexten laden.
**Akzeptanzkriterien:**
- ETM wird im Dialogkontext vor einer NPC-Antwort geladen.
- ETM wird für State-Updates geladen, wenn der State-Updater aufgrund neuer STM-Nachrichten läuft.
- ETM wird für Scene-Updates geladen, wenn der Scene-Updater aufgrund neuer STM-Nachrichten läuft.
- ETM wird nicht direkt für Bildgenerierung geladen.
- Bildgenerierung nutzt den aktuellen NPC-, State- und Scene-Kontext; relevante ETM-Inhalte wirken nur indirekt über State oder Scene ein.
- ETM wird nicht für die Anzeige des Initialkontexts in der Web-GUI geladen.
- Die Web-GUI verwendet für sichtbaren Initialkontext Charakterbeschreibung und Szene, nicht ETM.

**Referenzen:** `doc/requirements/sg-004-dynamischer-charakterzustand.md`, `doc/requirements/sg-006-dynamischer-scene-state.md`, `doc/requirements/sg-007-dreistufige-bildgenerierung.md`

### Begrenzung von Embedding-Requests
**Typ:** Nicht-funktional
**Beschreibung:** Das System muss Embedding-Requests für ETM-Retrieval begrenzen.
**Akzeptanzkriterien:**
- Ein ETM-Retrieval darf pro relevanter User-Nachricht höchstens eine Embedding-Query auslösen.
- State- und Scene-Updates dürfen ETM-Retrieval nur auslösen, wenn der jeweilige Updater tatsächlich läuft.
- Ohne vorhandenen ETM-Speicher wird kein Embedding-Request für ETM-Retrieval ausgelöst.
- Für Kontexte ohne ETM-Nutzung, insbesondere direkte Bildgenerierung, wird kein ETM-Retrieval-Embedding erzeugt.
- Leere oder rein technische Eingaben lösen kein ETM-Retrieval aus.

**Referenzen:** `doc/adr/004-modellstrategie.md`, `doc/adr/008-chroma-als-vector-datenbank.md`

### Trennung von Initialkontext und ETM
**Typ:** Randbedingung
**Beschreibung:** Das System muss ETM fachlich von statischem Initialkontext trennen.
**Akzeptanzkriterien:**
- Episoden sind abrufbare frühere Gesprächsabschnitte, keine kanonische Charakterbiografie.
- `relationship.md` ist statischer Initialkontext und keine abrufbare Episode.
- ETM-Treffer ergänzen den aktuellen Prompt, ersetzen den aktuellen State aber nicht.
- Die STM-Auslagerung schreibt ETM-Episoden, nicht `relationship.md`.
- State oder Scene werden nicht automatisch als eigenständige Memory-Artefakte fortgeschrieben.

**Referenzen:** `doc/requirements/sg-002-long-term-memory.md`, `doc/requirements/sg-004-dynamischer-charakterzustand.md`, `doc/requirements/sg-006-dynamischer-scene-state.md`

### Nutzung von State und Scene als Kontext
**Typ:** Randbedingung
**Beschreibung:** Das System darf State und Scene für ETM-Episodenbildung und Antwortgenerierung als Kontext nutzen, muss sie aber als abgeleitete Zustandsdaten behandeln.
**Akzeptanzkriterien:**
- State kann beim Schreiben einer Episode helfen, emotionale Einordnung vorsichtig zu formulieren.
- Scene kann beim Schreiben einer Episode helfen, situative Ereignisse einzuordnen.
- State- oder Scene-Inhalte werden nicht ohne Rückbindung an Gesprächsereignisse als dauerhafte Fakten gespeichert.
- Relevante Episoden dürfen spätere State- und Scene-Updates beeinflussen.

**Referenzen:** `doc/requirements/sg-004-dynamischer-charakterzustand.md`, `doc/requirements/sg-006-dynamischer-scene-state.md`

### NPC-Perspektive
**Typ:** Randbedingung
**Beschreibung:** Das System muss ETM-Episoden aus Sicht des aktiven NPC speichern.
**Akzeptanzkriterien:**
- ETM-Episoden beschreiben die Erinnerung des NPC an eine Situation.
- User-Aussagen werden als vom NPC wahrgenommene Hinweise formuliert, wenn sie nicht objektiv belegt sind.
- Emotionale Wirkung auf den NPC darf Teil einer ETM-Episode sein.
- ETM-Episoden werden nicht als externe Chat-Zusammenfassung formuliert.

**Referenzen:** `doc/requirements/sg-002-long-term-memory.md`, `doc/requirements/sg-003-short-term-memory.md`
