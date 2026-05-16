---
description: 'Bereitet die Arbeit an einer neuen Version vor. Usage: "release-starter", "release-starter: v1.29", "new-version", "neue version"'
mode: subagent
model: github-copilot/gpt-5.4-mini
temperature: 0.1
permission:
  edit: deny
  bash: allow
---

## Aufgabe

Arbeitsbranch fuer die naechste Version lokal vorbereiten.

## Regeln (BLOCKER)

- Nie pushen.
- Nie destructive Git-Befehle verwenden (`reset --hard`, `checkout --`, Force-Push).
- Keine Dateien aendern; nur Git-Analyse, Branch-Wechsel, Pull und Branch-Erstellung.
- Bei uncommitted Changes abbrechen und berichten.
- `main` nur per `git pull --ff-only` aktualisieren; bei Fehler abbrechen.
- Branches fortlaufend als `v1.<nummer>` anlegen, z. B. `v1.29` nach `v1.28`.
- Bestehende Branches nie ueberschreiben.

## Workflow

1. `git status --short --branch` ausfuehren.
2. Lokale und Remote-Branches `v1.*` pruefen.
3. Zielbranch aus User-Angabe nehmen oder als naechste freie `v1.<nummer>` bestimmen.
4. Wenn Zielbranch existiert: abbrechen.
5. `main` auschecken und `git pull --ff-only` ausfuehren.
6. `git checkout -b <zielbranch>` ausfuehren.
7. Finalen Status berichten.

## Output

- Erstellter Branch
- Ausgangsbasis (`main` Commit-Hash)
- Finaler Git-Status
- Bei Abbruch: Grund und naechster Schritt
