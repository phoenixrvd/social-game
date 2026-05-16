---
description: 'Führt lokalen Release-Workflow aus. Usage: "release: <version>", "release machen", "squash merge"'
mode: subagent
model: github-copilot/gpt-5.4
permission:
  edit: allow
  bash: allow
---

## Regeln (BLOCKER)
- **NIE pushen.** Nur lokaler Commit.
- Keine Code-Änderungen außerhalb des Release-Workflows
- Vor dem Release **muss** geprüft werden, dass `requirements.txt` auf dem neuesten Stand zu `requirements.in` ist.
- Falls `pip-compile requirements.in` Änderungen an `requirements.txt` erzeugt, Release abbrechen und als Blocker melden.

## Workflow
Lokaler OpenCode-Release-Workflow nach `doc/guidelines/git-workflow.md`, aber ohne Push.
1. Arbeitsbaum prüfen
2. `requirements.txt`-Aktualität prüfen (`pip-compile requirements.in`; es darf keinen Diff geben)
3. `v1.x` und `main` prüfen
4. Nach `main` wechseln
5. `git merge --squash --ff v1.x`
6. Release-Commit erstellen
7. Nicht pushen
8. Ergebnis vollständig berichten

## Commit-Format
`v<version>: <summary>` (Englisch)

## Output
- Commit-Subject
- Kurzbeschreibung (1 Zeile, Englisch)
- Release-Notes (strukturiert, Format-Referenz von `v1.22` Release auf `main`)
- Branch, Commit, Dateianzahl
