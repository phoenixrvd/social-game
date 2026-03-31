# ADR 002: Bewegungsdaten werden unter `.data/` gespeichert

**Status:** Akzeptiert  
**Datum:** 2026-03-15

## Kontext

Das Projekt trennt zwei Arten von Daten:

- **Initialdaten** (NPCs, Szenen, Prompts): versioniert im Repository, dienen als unveraenderte
  Ausgangsbasis und Fallback.
- **Bewegungsdaten** (Short-Term-Memory, LTM, aktualisierte States, generierte Bilder):
  entstehen zur Laufzeit, aendern sich dynamisch und sollen nicht in Git landen.

Ohne eine klare Trennung wuerden Laufzeitdaten die Projektdateien ueberschreiben,
was Debugging erschwert und Git-History verschmutzt.

## Entscheidung

Alle zur Laufzeit erzeugten oder veraenderten Daten werden ausschliesslich unter `.data/`
gespeichert. Das Verzeichnis wird nicht in Git versioniert (`.gitignore`).

**Ladestrategie:**

1. Daten werden zunächst aus den Projektverzeichnissen (`npcs/`, `scenes/`) geladen.
2. Danach wird geprueft, ob unter `.data/` eine aktuellere Version existiert.
3. Falls ja, ueberschreibt sie die geladenen Default-Werte.

**Schreibstrategie:**

- Speicheroperationen schreiben immer nach `.data/`, niemals in die Projektverzeichnisse.

**Konkrete Pfade:**

| Datenart           | Pfad                                                      |
|--------------------|-----------------------------------------------------------|
| NPC\-State         | `.data/npcs/<npc_id>/state.md`                            |
| Short\-Term\-Memory| `.data/npcs/<npc_id>/stm.jsonl`                           |
| Long\-Term\-Memory | `.data/npcs/<npc_id>/ltm.md`                              |
| Generiertes Bild   | `.data/npcs/<npc_id>/img.png`                             |
| Bild\-Backup       | `.data/npcs/<npc_id>/img_backup/img-<ts>.png`             |
| Szenendatei        | `.data/npcs/<npc_id>/<scene_id>/scene.md`                 |

Die Long-Term-Memory bleibt dateibasiert gespeichert, wird im Anwendungscode aber als Eigenschaft des jeweiligen `Npc` behandelt.
## Konsequenzen

- Projektdateien bleiben immer in einem sauberen, reproduzierbaren Zustand.
- Laufzeitdaten koennen einfach zurueckgesetzt werden (`.data/` loeschen).
- Debugging ist einfacher: Der aktuelle Stand liegt klar getrennt vom Default.
- Neue Umgebungen starten immer von denselben Initialwerten aus.

