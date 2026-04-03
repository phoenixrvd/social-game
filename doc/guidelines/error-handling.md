# Fehlerbehandlung

- `try { ... } catch { ... }` ohne sinnvolle Behandlung ist verboten.
- Fehler dürfen nicht still geschluckt werden.
- Fehler dürfen nicht künstlich umformuliert oder dekorativ neu verpackt werden, wenn dadurch die eigentliche Ursache verschleiert wird.
- Wenn keine sinnvolle fachliche Behandlung nötig ist, soll der Originalfehler erhalten bleiben.
- `catch` ist nur sinnvoll, wenn tatsächlich zusätzliche fachliche Reaktion erfolgt, z. B. UI-Zustand setzen, Polling stoppen oder eine konkrete Benutzerreaktion auslösen.

