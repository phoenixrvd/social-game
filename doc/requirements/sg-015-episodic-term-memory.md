---
state: implemented
---

# SG-015: Episodic Term Memory (ETM)

## Kontext
Das System soll sich an relevante frühere Gesprächsinhalte erinnern, auch wenn sie nicht mehr Teil des unmittelbaren Gesprächskontexts sind.
Dazu werden ältere Gesprächsabschnitte als kompakte Episoden festgehalten und bei passenden NPC-Antworten wieder berücksichtigt.
Statische Beziehungsgrundlagen bleiben davon getrennt; Episoden werden aus Sicht des aktiven NPC festgehalten.

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
**Beschreibung:** Das System muss frühere Episoden nur in fachlich passenden Situationen berücksichtigen.
**Akzeptanzkriterien:**
- Vor einer NPC-Antwort werden passende frühere Episoden berücksichtigt.
- Bei der Fortschreibung des aktuellen Charakterzustands werden passende frühere Episoden berücksichtigt, wenn neue Gesprächsinhalte dafür relevant sind.
- Bei der Fortschreibung der aktuellen Szene werden passende frühere Episoden berücksichtigt, wenn neue Gesprächsinhalte dafür relevant sind.
- Für die unmittelbare Bilderzeugung werden frühere Episoden nicht direkt herangezogen.
- Für die sichtbare Ausgangslage werden Charakterbeschreibung und Szene verwendet, nicht frühere Episoden.

**Referenzen:** `doc/requirements/sg-004-dynamischer-charakterzustand.md`, `doc/requirements/sg-006-dynamischer-scene-state.md`, `doc/requirements/sg-007-dreistufige-bildgenerierung.md`

### Begrenzung von Embedding-Requests
**Typ:** Nicht-funktional
**Beschreibung:** Das System muss die Berücksichtigung früherer Episoden sparsam und anlassbezogen halten.
**Akzeptanzkriterien:**
- Pro relevanter User-Nachricht wird die Berücksichtigung früherer Episoden höchstens einmal angestoßen.
- Bei der Fortschreibung des aktuellen Charakterzustands oder der aktuellen Szene werden frühere Episoden nur einbezogen, wenn dies fachlich erforderlich ist.
- Ohne vorhandene Episoden wird keine Berücksichtigung früherer Episoden ausgelöst.
- Für die unmittelbare Bilderzeugung werden keine früheren Episoden einbezogen.
- Leere oder rein technische Eingaben lösen keine Berücksichtigung früherer Episoden aus.

**Referenzen:** `doc/adr/004-modellstrategie.md`, `doc/adr/008-chroma-als-vector-datenbank.md`

### Trennung von Initialkontext und ETM
**Typ:** Randbedingung
**Beschreibung:** Das System muss frühere Gesprächsepisoden fachlich von statischem Ausgangskontext trennen.
**Akzeptanzkriterien:**
- Episoden sind frühere Gesprächserfahrungen und keine feste Charaktergrundlage.
- Statischer Ausgangskontext ist keine Episode.
- Berücksichtigte Episoden ergänzen den aktuellen Kontext, ersetzen aber nicht den aktuellen Charakterzustand.
- Beim Auslagern älterer Gesprächsinhalte entstehen Episoden, keine Änderungen am statischen Ausgangskontext.
- Der aktuelle Charakterzustand und die aktuelle Szene werden nicht allein durch ihre Fortschreibung zu eigenständigen Erinnerungen.

**Referenzen:** `doc/requirements/sg-002-long-term-memory.md`, `doc/requirements/sg-004-dynamischer-charakterzustand.md`, `doc/requirements/sg-006-dynamischer-scene-state.md`

### Nutzung von State und Scene als Kontext
**Typ:** Randbedingung
**Beschreibung:** Das System darf den aktuellen Charakterzustand und die aktuelle Szene zur Einordnung von Episoden und Antworten nutzen, muss sie aber als abgeleitete Momentaufnahme behandeln.
**Akzeptanzkriterien:**
- Der aktuelle Charakterzustand darf helfen, die emotionale Einordnung einer Episode vorsichtig zu formulieren.
- Die aktuelle Szene darf helfen, Ereignisse einer Situation einzuordnen.
- Inhalte aus aktuellem Charakterzustand oder aktueller Szene werden nicht ohne Bezug zu Gesprächsereignissen als dauerhafte Erinnerung festgehalten.
- Relevante Episoden dürfen spätere Fortschreibungen von Charakterzustand und Szene beeinflussen.

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
