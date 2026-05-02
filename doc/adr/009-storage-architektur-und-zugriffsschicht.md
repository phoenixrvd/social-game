---
state: accepted
---

# ADR-009: Storage-Architektur und Zugriffsschicht

## Status

accepted

## Kontext

* Die aktuelle Implementierung mischt Datenzugriff, Pfadauflösung, Formatierung und Fachlogik innerhalb einzelner Klassen.
* Das System nutzt überwiegend dateibasierte Speicherung (Markdown, YAML, JSONL, Images), ergänzt durch lokale SQLite-Datenbanken (z. B. für ETM).
* Die Nutzungsschnittstelle (`storage.*`) ist ergonomisch, jedoch droht bei weiterer Entwicklung eine zunehmende Vermischung von Verantwortlichkeiten.
* Zukünftig soll es möglich sein, einzelne Speichermechanismen (z. B. STM, ETM) durch alternative Implementierungen (z. B. Datenbank) zu ersetzen, ohne die Applikationslogik anzupassen.

## Entscheidung

Die Storage-Architektur folgt folgenden Prinzipien:

### Begriffe

* **Storage Facade** (`storage.*`)

  * Öffentliche API für Datenzugriff und Application State.
  * Einstiegspunkt für alle Datenoperationen.
  * Bildet eine fachlich benannte Baumstruktur ab.

* **Storage-Knoten** (z. B. `storage.npc`, `storage.npc.stm`, `storage.scene`, `storage.prompts`)

  * Repräsentieren fachliche Zugriffspunkte innerhalb der Baumstruktur.
  * Kapseln den Zugriff auf konkrete Ressourcen oder Speicherbereiche.
  * Stellen Inhalte und Zustände über Properties bereit.
  * Delegieren technische Persistenzdetails an spezialisierte Komponenten.

* **Store** (z. B. `StmStore`, `EtmStore`)

  * Persistenz-Adapter für konkrete Speichermechanismen wie JSONL, SQLite oder andere Datenbanken.
  * Kapselt technische Persistenzlogik.
  * Kennt Mapping zwischen Persistenzmodell und Domain-/DTO-Modell.

* **Domain-/DTO-Modell** (z. B. `Message`, `SessionState`)

  * Enthält strukturierte Daten und einfache, objektinterne Repräsentationslogik.
  * Ist von konkreten Speichermechanismen entkoppelt.

### Regeln

* Die Datenzugriffsstruktur wird als fachlicher Baum (`storage.*`) modelliert und bildet gleichzeitig den Application State ab.

* Datenzugriffe erfolgen ausschließlich über die Storage Facade.

  * Erlaubt:

    ```python
    messages = storage.npc.stm.latest
    prompt = storage.prompts.image_refresh
    storage.session.state = new_state
    ```
  * Nicht erlaubt:

    ```python
    SessionStorageItem(...)
    TextFile(...)
    StmStore(...)
    ```

* Direkte Instanziierung von Storage-Knoten, Stores oder technischen Datei-/Datenbankadaptern außerhalb des Storage-Layers ist nicht erlaubt.

* Limits und Standardauswahlen werden nicht im Caller gesetzt, wenn sie globale App-Konfiguration darstellen.

  * Beispiel: Die Anzahl der letzten STM-Nachrichten kommt aus der globalen Konfiguration und wird über eine fachlich benannte Property bereitgestellt:

    ```python
    messages = storage.npc.stm.latest
    ```

* Der Zugriff auf Inhalte und Zustände erfolgt über Properties, nicht über Getter-Methoden.

  * Beispiel:

    ```python
    prompt = storage.prompts.image_refresh
    storage.session.state = new_state
    ```

* Property-Setter sind nur erlaubt, wenn:

  * genau eine Ressource oder ein klar abgegrenzter Zustand geschrieben wird,
  * keine zusätzliche fachliche Logik ausgeführt wird,
  * keine Abhängigkeit zu anderen fachlichen Objekten besteht.

* In allen anderen Fällen sind explizite Methoden zu verwenden.

  * Beispiel:

    ```python
    storage.npc.stm.append(message)
    ```

* Persistierte Teile des Storage-Baums werden über fachlich benannte Storage-Knoten verwaltet.

  * Strukturierte Zustände werden als typisierte Modelle abgebildet, z. B. mit Pydantic.
  * Das Setzen von Properties oder Attributen eines persistierten Knotens triggert unmittelbar die Persistierung.
  * Begründung: In diesem System stellt der Storage-Baum den persistierten Application State dar. Änderungen am Zustand sollen unmittelbar konsistent gespeichert werden, um Seiteneffekte durch vergessene Persistierung zu vermeiden und den State jederzeit als Single Source of Truth im jeweiligen Speichermechanismus abzubilden.

* Domain-Objekte sind von Persistenzmodellen entkoppelt.

  * Beispiel:

    * `Message` ist Domain-/DTO-Modell.
    * `MessageRow` ist Persistenzmodell.

* Mapping zwischen Domain- und Persistenzmodellen erfolgt ausschließlich:

  * im Store oder
  * im Persistenzmodell selbst (z. B. `to_domain`, `from_domain`).

* Es wird keine separate Mapper-Schicht eingeführt, solange kein konkreter Bedarf besteht.

* Formatierungslogik gehört in Domain-Objekte, wenn sie ausschließlich auf eigene Daten zugreift und nur die Repräsentation dieses Objekts betrifft.

  * Beispiel:

    ```python
    message.text_short
    message.text_long
    ```

* Formatierungslogik gehört in dedizierte Formatter- oder Composer-Klassen, wenn:

  * mehrere Objekte beteiligt sind,
  * externe Konfiguration benötigt wird,
  * Kontext wie NPC, Scene oder Application State erforderlich ist,
  * aus einer Collection eine neue Repräsentation erzeugt wird.

* Storage-Knoten enthalten keine Geschäftslogik.

  * Sie dürfen ausschließlich delegieren oder einfache Zugriffskombinationen durchführen.
  * Fachliche Entscheidungen, insbesondere `if`/`else` mit fachlicher Bedeutung, gehören nicht in Storage-Knoten.

* Storage-Knoten-Funktionen enthalten keine Geschäftslogik und dienen primär der Delegation.

  * Als Richtwert sollen sie im Regelfall sehr kurz gehalten werden (≈ 1 Zeile).
  * In begründeten Ausnahmefällen, z. B. bei Speicher- oder Repräsentationsdelegation, sind bis zu drei Zeilen akzeptabel.

* Persistenzmechanismen dürfen ausgetauscht werden, ohne dass die Applikationslogik angepasst werden muss.

## Begründung

* Die fachliche Baumstruktur ermöglicht eine ergonomische und intuitive Nutzung, z. B. `storage.npc.stm.latest`.
* Storage-Knoten kapseln den Zugriff auf konkrete Ressourcen und unterstützen dadurch einen hexagonalen Architekturansatz.
* Die Trennung von Domain- und Persistenzmodellen verhindert langfristige Kopplung an konkrete Speichertechnologien.
* Die Beschränkung der Logik in Storage-Knoten reduziert Komplexität und verbessert Wartbarkeit.
* Die Verwendung von Properties erhöht Lesbarkeit und reduziert Boilerplate im Anwendungscode.

## Alternativen

### Alternative 1

* Vollständige Nutzung eines klassischen ORM (z. B. SQLAlchemy) mit Repository-Pattern.
* Verworfen, da dies zu erhöhter Komplexität (Session-Handling, Boilerplate) führt und nicht zum dateibasierten Großteil des Systems passt.

### Alternative 2

* Komplett funktionaler Ansatz ohne objektorientierte Storage-Knoten.
* Verworfen, da dies die Lesbarkeit und die ergonomische Nutzung der API verschlechtert.

### Alternative 3

* Vermischung von Domain-Logik und Persistenz (Active Record Stil).
* Verworfen, da dies langfristig zu schlechter Wartbarkeit und erhöhter Kopplung führt.

## Konsequenzen

* positiv: Klare Trennung von Verantwortlichkeiten zwischen Storage, Domain und Services.
* positiv: Austausch einzelner Speichermechanismen ohne Anpassung der Applikationslogik möglich.
* positiv: Sehr ergonomische und konsistente Public API.
* negativ: Zusätzliche Mapping-Logik zwischen Domain- und Persistenzmodellen.
* negativ: Disziplin erforderlich, um Logik nicht wieder in Storage-Knoten zu verschieben.

## Annahmen

* Die Mehrheit der Daten bleibt weiterhin dateibasiert.
* Nur ausgewählte Teile (z. B. ETM) werden in Datenbanken gespeichert.

## Offene Fragen

* Keine

## Referenzen

* ADR-001: Test-Strategie
* ADR-002: Datenspeicherung im .data-Verzeichnis
* ADR-003: Synchroner Update-Orchestrator
* ADR-006: Rolling-Releases ohne Kompatibilitätsschichten
* ADR-008: SQLite als lokal eingebetteter ETM-Store
* engine/storage.py
* engine/services/*
