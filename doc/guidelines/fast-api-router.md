# FastAPI Implementation Rules

## Router

* Router enthalten nur HTTP-Logik.
* Router rufen Services auf.
* Router enthalten keine Business-Logik.

## Services

* Business-Logik gehört in Services.
* Zustandsprüfungen gehören in Services.

## Pydantic

* Pydantic validiert nur Request-Struktur.
* Keine Business-Validierung in Pydantic.
* Keine Storage-, Service- oder Dateisystemzugriffe in Pydantic-Validatoren.

## OpenAPI

* Return-Type statt `response_model` verwenden.
* Kurze `summary` setzen.
* Fachliche Beschreibung in den Methoden-Docstring schreiben.
* Stabile und lesbare `operationId` verwenden.
* OpenAPI möglichst einfach halten.

## Naming

* Kurze Funktionsnamen innerhalb eines Routers verwenden.
* Pfade folgen der bestehenden API-Semantik.

## Struktur

* Kleine private Hilfsfunktionen sind erlaubt, wenn sie die Lesbarkeit verbessern.
* Request- und Response-Modelle dürfen im Router bleiben, solange sie nur dort verwendet werden.

## Architektur

* Nicht überabstrahieren.
* Keine generischen Frameworks, Resolver oder Factorys ohne konkreten Bedarf.
* Nur abstrahieren, wenn ein zweiter realer Anwendungsfall existiert.

## Qualität

Vor Abschluss prüfen:

* Return-Types korrekt
* Keine Business-Logik in Pydantic
* Router bleibt schlank
* Keine unnötige OpenAPI-Konfiguration
