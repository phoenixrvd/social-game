import { trustedHtml } from "./trusted-types.js"

function isMobileViewport() {
  return window.matchMedia("(max-width: 1023px)").matches
}

class SocialGameSceneImage extends HTMLElement {
  constructor() {
    super()
    this._state = {
      imageUrl: "",
      isExpanded: false,
    }
    this.$ = null
    this._lastFocusedElement = null
  }

  connectedCallback() {
    this.innerHTML = trustedHtml(`
      <div class="sg-image-pane">
        <div class="sg-image-empty sg-hidden">Kein Bild geladen</div>
        <div class="sg-image-frame">
          <div class="sg-image-content">
            <img class="sg-image-bg" src="data:," alt="Hintergrund" loading="lazy" decoding="async" fetchpriority="low" />
            <img class="sg-image-main" src="data:," alt="Szenenbild" role="button" tabindex="0" aria-label="Bild vergrößern" loading="lazy" decoding="async" />
          </div>
        </div>
      </div>

      <div class="sg-image-overlay" role="dialog" aria-modal="true" aria-label="Vergrößertes Szenenbild" tabindex="-1">
        <div class="sg-image-overlay-frame">
          <img class="sg-image-overlay-bg" src="data:," alt="Hintergrund" loading="lazy" decoding="async" />
          <img class="sg-image-overlay-main" src="data:," alt="Szenenbild" loading="lazy" decoding="async" />
        </div>
      </div>
    `)

    this.$ = {
      frame: this.querySelector(".sg-image-frame"),
      empty: this.querySelector(".sg-image-empty"),
      overlay: this.querySelector(".sg-image-overlay"),
      bg: this.querySelector(".sg-image-bg"),
      main: this.querySelector(".sg-image-main"),
      overlayBg: this.querySelector(".sg-image-overlay-bg"),
      overlayMain: this.querySelector(".sg-image-overlay-main"),
    }

    this.$.main.addEventListener("load", this.handleMainLoad.bind(this))
    this.$.main.addEventListener("error", this.handleMainError.bind(this))
    this.$.main.addEventListener("click", this.handleMainClick.bind(this))
    this.$.main.addEventListener("keydown", this.handleMainKeyDown.bind(this))
    this.$.overlay.addEventListener("click", this.handleOverlayClick.bind(this))
    this.$.overlay.addEventListener("keydown", this.handleOverlayKeyDown.bind(this))

    this.render()
  }

  setState(nextState = {}) {
    this._state = { ...this._state, ...nextState }
    this.render()
  }

  emit(name, detail = {}) {
    this.dispatchEvent(new CustomEvent(name, { bubbles: true, composed: true, detail }))
  }

  handleMainLoad() {
    this.emit("sg:image-load")
  }

  handleMainError() {
    this.emit("sg:image-error")
  }

  handleMainClick(event) {
    event.stopPropagation()
    if (!this._state.imageUrl || !isMobileViewport()) {
      return
    }
    this._lastFocusedElement = document.activeElement
    this.toggleExpanded()
  }

  handleMainKeyDown(event) {
    if (event.key !== "Enter" && event.key !== " ") {
      return
    }
    event.preventDefault()
    if (!this._state.imageUrl || !isMobileViewport()) {
      return
    }
    this._lastFocusedElement = document.activeElement
    this.toggleExpanded()
  }

  handleOverlayClick() {
    if (!this._state.isExpanded) {
      return
    }
    this.collapseOverlay()
  }

  handleOverlayKeyDown(event) {
    if (event.key !== "Escape") {
      return
    }
    event.preventDefault()
    this.collapseOverlay()
  }

  toggleExpanded() {
    if (!isMobileViewport()) {
      return
    }
    const nextExpanded = !this._state.isExpanded
    this.setState({ isExpanded: nextExpanded })
    this.emit("sg:image-expand-toggle", { expanded: nextExpanded })

    if (nextExpanded) {
      this.$.overlay.focus()
    }
  }

  collapseOverlay() {
    this.setState({ isExpanded: false })
    this.emit("sg:image-expand-toggle", { expanded: false })
    if (this._lastFocusedElement instanceof HTMLElement) {
      this._lastFocusedElement.focus()
    }
  }

  render() {
    const hasImage = typeof this._state.imageUrl === "string" && this._state.imageUrl.trim().length > 0
    const overlayIsOpen = Boolean(isMobileViewport() && this._state.isExpanded && hasImage)

    this.$.frame.classList.toggle("sg-hidden", !hasImage)
    this.$.empty.classList.toggle("sg-hidden", hasImage)
    this.$.overlay.classList.toggle("is-open", overlayIsOpen)

    if (!hasImage) {
      return
    }

    if (this.$.main.getAttribute("src") === this._state.imageUrl) {
      return
    }

    ;[this.$.bg, this.$.main, this.$.overlayBg, this.$.overlayMain].forEach((img) => {
      img.src = this._state.imageUrl
    })
  }
}

customElements.get("sg-scene-image") || customElements.define("sg-scene-image", SocialGameSceneImage)
