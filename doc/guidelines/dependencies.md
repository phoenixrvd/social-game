# Dependency Management

## Regeln

- Direkte Dependencies nur in `requirements.in` pflegen.
- Direkte Dependencies in `requirements.in` und Dev-Dependencies in `requirements.dev.txt` mit Mindestversionen `>=` pflegen (Baseline = aktuell eingesetzte Version).
- `requirements.txt` nie manuell bearbeiten; immer aus `requirements.in` generieren.
- Neue Libraries nur einführen, wenn fachlich notwendig.
- Transitive Dependencies nur bei bewusstem Override/Pin in `requirements.in` eintragen.

## Befehle

- `pip-compile requirements.in` - erzeugt/aktualisiert das reproduzierbare Lockfile `requirements.txt`.
- `pip install -r requirements.txt` - installiert den gelockten Produktionsstand.
- `pip-sync requirements.txt` (optional) - synchronisiert eine bestehende Umgebung exakt auf den Lockfile-Stand.
- `pip install -r requirements.dev.txt` - installiert zusaetzlich Dev-Tools fuer Entwicklung und Tests.

## Update-Ablauf

1. Gewuenschte direkte oder Dev-Dependency in `requirements.in` bzw. `requirements.dev.txt` auf neue Mindestversion `>=` anheben.
2. Lockfile neu erzeugen: `pip-compile requirements.in`.
3. Umgebung aktualisieren: `pip install -r requirements.txt` (optional sauberer: `pip-sync requirements.txt`).
4. Tests ausfuehren und Ergebnis pruefen.
5. Wenn alles stabil ist, neue eingesetzte Version als Baseline in `requirements.in`/`requirements.dev.txt` beibehalten.
