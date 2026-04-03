# Coding Rules

## Methoden und Kontrollfluss
- Vermeide zu lange Methoden.
- Vermeide Verschachtelungen von Statements über mehr als drei Ebenen.
- Zerlege komplexe Logik in kleinere, fachlich sinnvolle Bausteine.
- Vermeide „Blah Blah"-Code ohne fachlichen Mehrwert.
- Bevorzuge bei einfachen Guard-Checks die Kurzform, wenn sie eindeutig lesbar bleibt.

## Kontextauflösung
- Löse aktiven `npc_id`/`scene_id`-Kontext, wenn möglich, direkt über den `SessionStore` auf, statt IDs über viele Schichten durchzureichen.
- Bevorzuge für operationen auf dem aktiven NPC-Szenen-Kontext Store-Methoden ohne `npc_id`/`scene_id`-Parameter.

## Wrapper und Proxy-Methoden
- Vermeide reine Proxy-Methoden.
- Vermeide Ein-Zeilen-Methoden, die keine zusätzliche Funktionalität bringen und nur bestehende Aufrufe umwrapen.
- Wenn eine Methode nur delegiert, soll die Logik direkt an der eigentlichen Verwendungsstelle stehen.
- Vermeide Proxy-Getter für DOM-Elemente wie `frameElement`, `inputElement` oder ähnliche reine `querySelector`-Weiterreichungen.
- Wenn ein DOM-Element nur lokal in einer Methode gebraucht wird, soll es dort direkt abgefragt werden.
- Vermeide freie Hilfsfunktionen, die nur `this` oder ein anderes Element durchreichen, um darauf direkt `dispatchEvent(...)` auszuführen.
- In Web Components soll Event-Dispatch direkt über die Komponente erfolgen, z. B. über `this.emit(...)` statt über Hilfsfunktionen mit `element`-Parameter.

## Konstanten und Literale
- Verwende globale Konstanten nur, wenn ein identischer Wert mehr als zweimal im selben Modul vorkommt.
- Wenn ein String oder eine Zahl nur ein- oder zweimal vorkommt, nutze direkte Literale.
- Wenn ein Literal oder eine Magic Number ohne Kontext unklar ist, benenne ihn zuerst lokal in einer Variable.
- Bevorzuge lokale Benennung für Verständlichkeit; globales Auslagern nur bei echter Wiederverwendung.

## CSS-Struktur und Reihenfolge
- Ordne CSS-Dateien in dieser Reihenfolge: Variablen (`:root`, Theme-Varianten), generische Element-Selektoren, generische IDs/Klassen, komponentenspezifische Klassen, Media Queries.
- Variablen stehen immer am Anfang der Datei.
- Generische Selektoren und Utilities dürfen nicht mit komponentenspezifischen Blöcken vermischt werden.
- Komponentenspezifische Klassen werden pro Komponente gruppiert.
- Innerhalb eines Komponentenblocks werden Klassen alphabetisch nach Selektorname sortiert.
- Media Queries stehen am Ende der Datei und folgen derselben Struktur innerhalb des Blocks.

## Unbenutzter Code
- Entferne ungenutzte Blöcke sofort.
- Entferne echten Dead Code, unnötige Wrapper und ungenutzte Getter konsequent.
- False Positives der IDE dürfen nicht mit echtem Dead Code verwechselt werden.

## Darstellung von Markup und langen Literalen
- Lagere größere SVG-Blöcke in benannte Konstanten aus.
- Vermeide lange Inline-SVGs in Render-Methoden oder Templates.
- Allgemein sollen große Markup-Blöcke so strukturiert werden, dass Dateien ohne langes Scrollen verständlich bleiben.
