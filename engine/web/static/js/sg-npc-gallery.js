import "./sg-context-gallery.js"

class SocialGameNpcGallery extends HTMLElement {
  constructor() {
    super()
  }

  connectedCallback() {
    this.innerHTML = `<sg-context-gallery data-context-type="npc"></sg-context-gallery>`
  }
}

customElements.get("sg-npc-gallery") || customElements.define("sg-npc-gallery", SocialGameNpcGallery)


