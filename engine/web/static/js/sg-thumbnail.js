import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"

function isMobileViewport() {
  return window.matchMedia("(max-width: 1023px)").matches
}

class SocialGameThumbnail extends HTMLElement {
  constructor() {
    super()
    this._state = {
      imageUrl: "",
      isLoading: false,
      isExpanded: false,
    }

    this.$ = {}
    this._lastFocusedElement = null
  }

  connectedCallback() {
    this.innerHTML = this.buildMarkup()
    this.cacheElements()
    this.registerDomEvents()
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  buildMarkup() {
    return `
      <div class="sg-image-frame">
        <div class="sg-image-content">
          <img class="sg-image-bg" src="data:," alt="Hintergrund" loading="lazy" decoding="async" fetchpriority="low" />
          <img class="sg-image-main" src="data:," alt="Szenenbild" role="button" tabindex="0" aria-label="Bild vergroessern" loading="lazy" decoding="async" />
        </div>
      </div>

      <div class="sg-image-overlay" role="dialog" aria-modal="true" aria-label="Vergroessertes Szenenbild" tabindex="-1">
        <div class="sg-image-overlay-frame">
          <img class="sg-image-overlay-bg" src="data:," alt="Hintergrund" loading="lazy" decoding="async" />
          <img class="sg-image-overlay-main" src="data:," alt="Szenenbild" loading="lazy" decoding="async" />
        </div>
      </div>
    `
  }

  cacheElements() {
    this.$ = {
      frame: this.querySelector(".sg-image-frame"),
      overlay: this.querySelector(".sg-image-overlay"),
      bg: this.querySelector(".sg-image-bg"),
      main: this.querySelector(".sg-image-main"),
      overlayBg: this.querySelector(".sg-image-overlay-bg"),
      overlayMain: this.querySelector(".sg-image-overlay-main"),
    }
  }

  registerDomEvents() {
    this.$.main.addEventListener("error", this.handleMainError.bind(this))
    this.$.main.addEventListener("click", this.handleMainClick.bind(this))
    this.$.main.addEventListener("keydown", this.handleMainKeyDown.bind(this))
    this.$.overlay.addEventListener("click", this.handleOverlayClick.bind(this))
    this.$.overlay.addEventListener("keydown", this.handleOverlayKeyDown.bind(this))
  }

  registerSubscriptions() {
    const subscriptions = [
      ["imageUrl", this.onImageUrlChanged.bind(this)],
      ["isImageExpanded", this.onImageExpandedChanged.bind(this)],
      ["isImageRefreshLoading", this.onImageRefreshLoadingChanged.bind(this)],
    ]

    for (const [key, listener] of subscriptions) {
      appStore.subscribe(key, listener)
    }
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.imageUrl = typeof state.imageUrl === "string" ? state.imageUrl : ""
    this._state.isExpanded = Boolean(state.isImageExpanded)
    this._state.isLoading = Boolean(state.isImageRefreshLoading)
  }

  onImageUrlChanged(imageUrl) {
    this._state.imageUrl = typeof imageUrl === "string" ? imageUrl : ""
    this.render()
  }

  onImageExpandedChanged(isImageExpanded) {
    this._state.isExpanded = Boolean(isImageExpanded)
    this.render()
  }

  onImageRefreshLoadingChanged(isImageRefreshLoading) {
    this._state.isLoading = Boolean(isImageRefreshLoading)
    this.render()
  }

  handleMainError(event) {
    event.stopPropagation()
    this.$.main.classList.remove("is-updated")
    this.$.overlayMain.classList.remove("is-updated")
    appActions.setImageError()
  }

  handleMainClick(event) {
    event.stopPropagation()
    this.requestExpandFromUserGesture()
  }

  handleMainKeyDown(event) {
    if (event.key !== "Enter" && event.key !== " ") {
      return
    }

    event.preventDefault()
    this.requestExpandFromUserGesture()
  }

  handleOverlayClick() {
    if (!this._state.isExpanded) {
      return
    }

    this.requestCollapseFromUserGesture()
  }

  handleOverlayKeyDown(event) {
    if (event.key !== "Escape") {
      return
    }

    event.preventDefault()
    this.requestCollapseFromUserGesture()
  }

  requestExpandFromUserGesture() {
    if (!this.canOpenOverlay()) {
      return
    }

    this._lastFocusedElement = document.activeElement
    appActions.toggleImageExpand(true)
  }

  requestCollapseFromUserGesture() {
    appActions.toggleImageExpand(false)
    this.restoreFocus()
  }

  canOpenOverlay() {
    return Boolean(this._state.imageUrl && isMobileViewport())
  }

  restoreFocus() {
    if (this._lastFocusedElement instanceof HTMLElement) {
      this._lastFocusedElement.focus()
    }
  }

  render() {
    const hasImage = typeof this._state.imageUrl === "string" && this._state.imageUrl.trim().length > 0
    const overlayIsOpen = Boolean(isMobileViewport() && this._state.isExpanded && hasImage)
    const showLoadingState = Boolean(this._state.isLoading && hasImage)
    const isSceneThumbnail = this.classList.contains("sg-scene-thumbnail")

    this.$.frame.classList.toggle("sg-hidden", !hasImage)
    this.$.frame.classList.toggle("is-loading", showLoadingState && !isSceneThumbnail)
    this.$.overlay.classList.toggle("is-open", overlayIsOpen)

    if (overlayIsOpen) {
      this.$.overlay.focus()
    }

    if (!hasImage) {
      return
    }

    const currentSrc = this.$.main.getAttribute("src") || ""
    if (currentSrc === this._state.imageUrl) {
      return
    }

    this.$.main.classList.add("is-updated")
    this.$.overlayMain.classList.add("is-updated")

    window.setTimeout(() => {
      this.$.main.classList.remove("is-updated")
      this.$.overlayMain.classList.remove("is-updated")
    }, 520)

    ;[this.$.bg, this.$.main, this.$.overlayBg, this.$.overlayMain].forEach((img) => {
      img.src = this._state.imageUrl
    })
  }
}

customElements.get("sg-thumbnail") || customElements.define("sg-thumbnail", SocialGameThumbnail)
