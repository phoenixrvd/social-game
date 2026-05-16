# Deployment

- [BLOCKER] Produktionsnahe Container laufen immer als non-root Runtime-User.
- [BLOCKER] Runtime-Images enthalten keine unnoetigen Build- oder Debug-Tools.
- [BLOCKER] Schreibrechte werden nur fuer explizit benoetigte Runtime-Pfade vergeben.
- [BLOCKER] Secrets (z. B. `.env`, Keys, Credentials) duerfen nie ins Image kopiert werden.
- [WARNING] Runtime-Isolation via `read_only`, `cap_drop: ["ALL"]` und `no-new-privileges:true` ist Standard, sofern fachlich kompatibel.
