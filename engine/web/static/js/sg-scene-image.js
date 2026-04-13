import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"

function isMobileViewport() {
  return window.matchMedia("(max-width: 1023px)").matches
}

class SocialGameSceneImage extends HTMLElement {
  constructor() {
    super()
    this._state = {
      imageUrl: "",
      isExpanded: false,
      isLoading: false,
    }
    this.$ = null
    this._lastFocusedElement = null
    this._shouldAnimateNextImage = false
    this._updateAnimationTimer = null
  }

  connectedCallback() {
    this.innerHTML = `
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
    `

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

    const subscriptions = [
      ["imageUrl", this.onImageUrlChanged.bind(this)],
      ["isImageExpanded", this.onImageExpandedChanged.bind(this)],
      ["isImageRefreshLoading", this.onImageRefreshLoadingChanged.bind(this)],
    ]

    for (const [key, listener] of subscriptions) {
      appStore.subscribe(key, listener)
    }

    this.render()
  }

  disconnectedCallback() {
    if (this._updateAnimationTimer !== null) {
      clearTimeout(this._updateAnimationTimer)
      this._updateAnimationTimer = null
    }
  }

  handleMainLoad() {
    if (this._shouldAnimateNextImage) {
      this.$.main.classList.add("is-updated")
      this.$.overlayMain.classList.add("is-updated")
      this._shouldAnimateNextImage = false
      if (this._updateAnimationTimer !== null) {
        clearTimeout(this._updateAnimationTimer)
      }
      this._updateAnimationTimer = window.setTimeout(() => {
        this.$.main.classList.remove("is-updated")
        this.$.overlayMain.classList.remove("is-updated")
        this._updateAnimationTimer = null
      }, 520)
    }
  }

  handleMainError() {
    this._shouldAnimateNextImage = false
    this.$.main.classList.remove("is-updated")
    this.$.overlayMain.classList.remove("is-updated")
    appActions.setImageError()
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
    appActions.toggleImageExpand(nextExpanded)

    if (nextExpanded) {
      this.$.overlay.focus()
    }
  }

  collapseOverlay() {
    appActions.toggleImageExpand(false)
    if (this._lastFocusedElement instanceof HTMLElement) {
      this._lastFocusedElement.focus()
    }
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

  render() {
    const hasImage = typeof this._state.imageUrl === "string" && this._state.imageUrl.trim().length > 0
    const overlayIsOpen = Boolean(isMobileViewport() && this._state.isExpanded && hasImage)
    const showLoadingState = Boolean(this._state.isLoading && hasImage)

    this.$.frame.classList.toggle("sg-hidden", !hasImage)
    this.$.empty.classList.toggle("sg-hidden", hasImage)
    this.$.overlay.classList.toggle("is-open", overlayIsOpen)
    this.$.frame.classList.toggle("is-loading", showLoadingState)

    if (!hasImage) {
      return
    }

    const currentSrc = this.$.main.getAttribute("src") || ""
    if (currentSrc === this._state.imageUrl) {
      return
    }

    this._shouldAnimateNextImage = Boolean(currentSrc && currentSrc !== "data:,")

    ;[this.$.bg, this.$.main, this.$.overlayBg, this.$.overlayMain].forEach((img) => {
      img.src = this._state.imageUrl
    })
  }
}

customElements.get("sg-scene-image") || customElements.define("sg-scene-image", SocialGameSceneImage)
