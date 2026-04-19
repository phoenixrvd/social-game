import "./sg-context-gallery.js"

class SocialGameSceneGallery extends HTMLElement {
  constructor() {
    super()
  }

  connectedCallback() {
    this.innerHTML = `<sg-context-gallery data-context-type="scene"></sg-context-gallery>`
  }
}

customElements.get("sg-scene-gallery") || customElements.define("sg-scene-gallery", SocialGameSceneGallery)

