import "./sg-context-gallery.js"

class SocialGameInputContext extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <section class="sg-settings-section">
        <div class="sg-session-row">
          <sg-context-gallery data-context-type="npc"></sg-context-gallery>
          <sg-context-gallery data-context-type="scene"></sg-context-gallery>
        </div>
      </section>
    `
  }
}

customElements.get("sg-input-context") || customElements.define("sg-input-context", SocialGameInputContext)






