# React Frontend

## Komponenten

- [BLOCKER] Komponenten sind funktionale React-Komponenten; keine Klassen-Komponenten
- [BLOCKER] Kein direkter DOM-Zugriff (`querySelector` verboten); State und Refs über React-APIs
- [BLOCKER] Kommunikation zwischen Komponenten ausschließlich über Props und Callbacks (kein direktes DOM-Event-Bubbling zwischen Komponenten)

## CSS-Architektur

- [BLOCKER] CSS folgt einem **Mobile-First**-Ansatz: Basis-Styles gelten für mobile Portrait-Ansicht; größere Breakpoints überschreiben per `min-width`
- [BLOCKER] Media Queries stehen am **Ende der Datei** in dieser Reihenfolge: `min-width`-Breakpoints (aufsteigend), Orientierungs-Queries, `prefers-reduced-motion`
- [BLOCKER] Animationen (`@keyframes`) und Custom Properties (`@property`) stehen am **Anfang der Datei**, direkt nach den Variablen-Blöcken (`:root`, `[data-theme]`)
- [BLOCKER] UI-Animationen und Transition-Logik in CSS umsetzen; keine JavaScript-Animationen, außer wenn technisch zwingend erforderlich und im PR begründet
- [BLOCKER] Keine `max-width`-Breakpoints für mobile Stile, wenn dieselben Regeln als Basis in den globalen Bereich gehören
- [WARNING] `max-width`-Queries nur für echte Ausnahmen (z. B. Landscape-Override), nicht als primäre mobile Abgrenzung
- [WARNING] CSS-Variablen als Tokens für Theme und Layout verwenden; keine hardcodierten Farb- oder Größenwerte außerhalb von `:root`/`[data-theme]`
