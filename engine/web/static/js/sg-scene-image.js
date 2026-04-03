import { trustedHtml } from "./trusted-types.js"

class SocialGameSceneImage extends HTMLElement {
  constructor() {
    super()
    this._state = {
      imageUrl: "",
      isExpanded: false,
    }
    this._boundHandleMainLoad = this.handleMainLoad.bind(this)
    this._boundHandleMainError = this.handleMainError.bind(this)
    this._boundHandleMainClick = this.handleMainClick.bind(this)
    this._boundHandleMainKeyDown = this.handleMainKeyDown.bind(this)
    this._boundHandleOverlayClick = this.handleOverlayClick.bind(this)
    this._boundHandleOverlayKeyDown = this.handleOverlayKeyDown.bind(this)
    this._listeners = [
      [".sg-image-main", "load", this._boundHandleMainLoad],
      [".sg-image-main", "error", this._boundHandleMainError],
      [".sg-image-main", "click", this._boundHandleMainClick],
      [".sg-image-main", "keydown", this._boundHandleMainKeyDown],
      [".sg-image-overlay", "click", this._boundHandleOverlayClick],
      [".sg-image-overlay", "keydown", this._boundHandleOverlayKeyDown],
    ]
    this._lastFocusedElement = null
  }

  connectedCallback() {
    if (!this.querySelector(".sg-image-pane")) {
      this.innerHTML = trustedHtml(`
        <div class="sg-image-pane">
          <div class="sg-image-empty sg-hidden">Kein Bild geladen</div>
          <div class="sg-image-frame">
            <div class="sg-image-content">
              <img class="sg-image-bg" src="data:," alt="Hintergrund" />
              <img class="sg-image-main" src="data:," alt="NPC" />
            </div>
          </div>
        </div>

        <div class="sg-image-overlay">
          <div class="sg-image-overlay-frame">
            <img class="sg-image-overlay-bg" src="data:," alt="Hintergrund" />
            <img class="sg-image-overlay-main" src="data:," alt="NPC" />
          </div>
        </div>
      `)
    }

    const mainImage = this.querySelector(".sg-image-main")
    const backgroundImage = this.querySelector(".sg-image-bg")
    const overlayBackgroundImage = this.querySelector(".sg-image-overlay-bg")
    const overlayMainImage = this.querySelector(".sg-image-overlay-main")
    const overlayElement = this.querySelector(".sg-image-overlay")

    if (mainImage) {
      mainImage.setAttribute("role", "button")
      mainImage.setAttribute("tabindex", "0")
      mainImage.setAttribute("aria-label", "Bild vergroessern")
      mainImage.setAttribute("loading", "lazy")
      mainImage.setAttribute("decoding", "async")
    }
    backgroundImage?.setAttribute("loading", "lazy")
    backgroundImage?.setAttribute("decoding", "async")
    backgroundImage?.setAttribute("fetchpriority", "low")
    overlayBackgroundImage?.setAttribute("loading", "lazy")
    overlayBackgroundImage?.setAttribute("decoding", "async")
    overlayMainImage?.setAttribute("loading", "lazy")
    overlayMainImage?.setAttribute("decoding", "async")

    if (overlayElement) {
      overlayElement.setAttribute("role", "dialog")
      overlayElement.setAttribute("aria-modal", "true")
      overlayElement.setAttribute("aria-label", "Vergroessertes NPC-Bild")
      overlayElement.setAttribute("tabindex", "-1")
    }

    this._listeners.forEach(([selector, eventName, handler]) => {
      this.querySelector(selector)?.addEventListener(eventName, handler)
    })

    this.render()
  }

  disconnectedCallback() {
    this._listeners.forEach(([selector, eventName, handler]) => {
      this.querySelector(selector)?.removeEventListener(eventName, handler)
    })
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
    this._lastFocusedElement = document.activeElement
    this.emit("sg:image-expand-toggle", { expanded: !this._state.isExpanded })
  }

  handleMainKeyDown(event) {
    if (event.key !== "Enter" && event.key !== " ") {
      return
    }
    event.preventDefault()
    this._lastFocusedElement = document.activeElement
    this.emit("sg:image-expand-toggle", { expanded: !this._state.isExpanded })
  }

  handleOverlayClick() {
    if (!this._state.isExpanded) {
      return
    }
    this.emit("sg:image-expand-toggle", { expanded: false })
  }

  handleOverlayKeyDown(event) {
    if (event.key !== "Escape") {
      return
    }
    event.preventDefault()
    this.emit("sg:image-expand-toggle", { expanded: false })
  }

  render() {
    const hasImage = Boolean(this._state.imageUrl)
    const frameElement = this.querySelector(".sg-image-frame")
    const emptyElement = this.querySelector(".sg-image-empty")
    const overlayElement = this.querySelector(".sg-image-overlay")
    const overlayWasOpen = overlayElement?.classList.contains("is-open") ?? false
    const overlayIsOpen = Boolean(this._state.isExpanded && hasImage)
    frameElement?.classList.toggle("sg-hidden", !hasImage)
    emptyElement?.classList.toggle("sg-hidden", hasImage)
    overlayElement?.classList.toggle("is-open", overlayIsOpen)

    if (!overlayWasOpen && overlayIsOpen) {
      overlayElement?.focus()
    } else if (overlayWasOpen && !overlayIsOpen && this._lastFocusedElement instanceof HTMLElement) {
      this._lastFocusedElement.focus()
    }

    if (!hasImage) {
      return
    }

    const backgroundImage = this.querySelector(".sg-image-bg")
    const mainImage = this.querySelector(".sg-image-main")
    const overlayBackgroundImage = this.querySelector(".sg-image-overlay-bg")
    const overlayMainImage = this.querySelector(".sg-image-overlay-main")
    if (!backgroundImage || !mainImage || !overlayBackgroundImage || !overlayMainImage) {
      return
    }

    if (backgroundImage.getAttribute("src") !== this._state.imageUrl) {
      backgroundImage.src = this._state.imageUrl
    }
    if (mainImage.getAttribute("src") !== this._state.imageUrl) {
      mainImage.src = this._state.imageUrl
    }
    if (overlayBackgroundImage.getAttribute("src") !== this._state.imageUrl) {
      overlayBackgroundImage.src = this._state.imageUrl
    }
    if (overlayMainImage.getAttribute("src") !== this._state.imageUrl) {
      overlayMainImage.src = this._state.imageUrl
    }
  }
}

customElements.get("sg-scene-image") || customElements.define("sg-scene-image", SocialGameSceneImage)
