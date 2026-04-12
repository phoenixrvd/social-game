# Coding Rules

## Komplexität

- [BLOCKER] Methoden max. 30 Zeilen (Richtwert)
- [BLOCKER] Verschachtelung max. 2–3 Ebenen
- [BLOCKER] Komplexe Logik in kleinere, fachlich sinnvolle Einheiten zerlegen
- [WARNING] Einfache Guard-Checks kompakt, aber klar lesbar halten

## Struktur

- [BLOCKER] Code muss lokal verständlich sein (keine unnötigen Kontextsprünge)
- [BLOCKER] Konstruktoren nutzen kein keyword-only `*`-Pattern
- [WARNING] Zusammengehörige Logik räumlich gruppieren

## Kontext

- [BLOCKER] Kontext nicht unnötig durch mehrere Schichten weiterreichen
- [BLOCKER] Klassen instanziieren benötigte Stores und Services selbst; keine Store-/Service-Übergabe über Konstruktorparameter
- [WARNING] Kontext möglichst nah an der Verwendung auflösen

## Wrapper / Delegation

- [BLOCKER] Keine Proxy- oder Delegationsmethoden ohne eigene Logik
- [BLOCKER] Keine Ein-Zeilen-Wrapper ohne Mehrwert

## Konstanten

- [BLOCKER] Globale Konstanten nur bei echter Wiederverwendung (>2x im Modul)
- [WARNING] Unklare Literale lokal benennen

## Dead Code

- [BLOCKER] Unbenutzten Code sofort entfernen
- [BLOCKER] Code, der nur noch von Tests oder Doku referenziert wird, gilt als unbenutzt, sofern er keine bewusst erhaltene öffentliche Schnittstelle ist
- [WARNING] IDE-Warnungen prüfen, aber nicht blind übernehmen

## Naming

- [WARNING] Namen müssen den Zweck klar widerspiegeln
- [WARNING] Keine unnötigen Abkürzungen
