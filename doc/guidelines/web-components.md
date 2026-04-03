# Web Components

- `connectedCallback()` und `disconnectedCallback()` sind gültige Lifecycle-Hooks von Web Components und dürfen nicht wegen falscher „unused"-Warnungen entfernt werden.
- Lifecycle-Hooks sollen nur dann bestehen bleiben, wenn sie tatsächlich Initialisierung oder Aufräumen übernehmen.
- Baue keine zusätzlichen Abstraktionsschichten oder Interfaces nur, um Lifecycle-Hooks künstlich „abzusichern".
- Guard-Checks bei der Registrierung von Web Components werden standardmäßig in der Kurzform mit `||` geschrieben, z. B. `customElements.get("sg-chat") || customElements.define("sg-chat", SocialGameChat)`.
- Parent-Komponenten dürfen nicht per `querySelector` auf interne DOM-Strukturen von Child-Web-Components zugreifen (z. B. `.querySelector(".sg-chat-messages")`).
- Kommunikation zwischen Parent- und Child-Komponenten erfolgt über öffentliche APIs (Properties/Methoden) und `CustomEvent`s; internes Child-DOM ist kein stabiler API-Vertrag.

