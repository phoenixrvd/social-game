import "./sg-context-gallery.js"

class SocialGameInputContext extends HTMLElement {
  connectedCallback() {
    this.innerHTML = /*html*/ `
      <section class="sg-settings-section">
        <div class="sg-session-row">
          <sg-context-gallery data-context-type="npc"></sg-context-gallery>
          <sg-context-gallery data-context-type="scene"></sg-context-gallery>
        </div>
      </section>
    `

    const sceneGallery = this.querySelector('sg-context-gallery[data-context-type="scene"]')
    sceneGallery.addEventListener("createSceneRequested", () => {
      this.dispatchEvent(new CustomEvent("createSceneRequested", { bubbles: true, composed: true }))
    })

    const npcGallery = this.querySelector('sg-context-gallery[data-context-type="npc"]')
    npcGallery.addEventListener("createNpcRequested", () => {
      this.dispatchEvent(new CustomEvent("createNpcRequested", { bubbles: true, composed: true }))
    })
  }
}

customElements.get("sg-input-context") || customElements.define("sg-input-context", SocialGameInputContext)

