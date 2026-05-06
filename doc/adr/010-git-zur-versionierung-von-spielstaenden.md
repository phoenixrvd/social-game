---
state: accepted
---

# ADR-010: Git zur Versionierung von Spielständen

## Status
accepted

## Kontext
- SG-009 fordert eine nachvollziehbare Spielstandshistorie für Speicherung und Wiederherstellung des aktiven Laufzeitdatenbestands unter `.data/<npc>`.
- Dafür werden wiederherstellbare Checkpoints für Dateien in unterschiedlichen Formaten benötigt.

## Entscheidung
- Spielstände unter `.data/<npc>` werden für SG-009 mit Git versioniert.

## Begründung
- Git ist eine einfache Möglichkeit, Dateien in unterschiedlichen Formaten zu versionieren.
- Git ist für den vorgesehenen Anwendungsfall platzsparend und schnell.
- Das Risiko bei binären Daten wie Bildern und Datenbanken wird aufgrund der geringen gespeicherten Datenmenge bewusst akzeptiert.

## Alternativen
### Alternative 1
- Spielstände als vollständige Snapshot-Kopien pro Speichervorgang in separaten Verzeichnissen ablegen.
- Verworfen, weil dies bei mehreren Dateiformaten zusätzlichen Verwaltungsaufwand erzeugt und weniger platzsparend ist.
### Alternative 2
- Spielstandshistorie in einer eigenen Datenbank verwalten.
- Verworfen, weil dies für die Versionierung eines dateibasierten Bestands unnötige technische Komplexität einführt.
### Alternative 3
- Ein eigenes dateibasiertes Versionsformat für Spielstände implementieren.
- Verworfen, weil Git die benötigte Versionierung bereits einfach bereitstellt.

## Konsequenzen
- positiv: Der vollständige Laufzeitdatenbestand unter `.data/<npc>` kann als nachvollziehbare Historie versioniert werden.
- positiv: Unterschiedliche Dateiformate können ohne separates Versionskonzept gemeinsam gespeichert werden.
- negativ: Binäre Daten wie Bilder und Datenbanken können in Git nachteilig sein.
- offen: Wenn die Menge binärer Daten deutlich wächst, muss die Eignung von Git erneut bewertet werden.

## Annahmen
- Die Menge der gespeicherten binären Daten bleibt gering.

## Offene Fragen
- Keine

## Referenzen
- `doc/requirements/sg-009-git-basierte-spielstandshistorie.md`
- `doc/adr/002-datenspeicherung-data-verzeichnis.md`

