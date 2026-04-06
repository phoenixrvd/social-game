# Error Handling

## Grundregeln

- [BLOCKER] Kein `try/catch` ohne sinnvolle Behandlung
- [BLOCKER] Fehler dürfen nicht still geschluckt werden
- [BLOCKER] Originalfehler nicht ersetzen oder verändern, wenn keine fachliche Transformation erfolgt

## Verwendung von catch

- [BLOCKER] `catch` nur verwenden, wenn eine fachliche Reaktion erfolgt
- [WARNING] Ohne fachliche Behandlung Fehler unverändert weitergeben

## Fehlerarten

- [BLOCKER] Technische Fehler nicht als fachliche Fehler umdeuten
- [BLOCKER] Technische Implementierungsfehler nicht durch Exception-Handling kaschieren

## Eigene Exceptions

- [BLOCKER] Eigene Exception-Logik nur bei fachlicher Bedeutung einsetzen