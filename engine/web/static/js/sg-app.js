import "./sg-chat.js"
import "./sg-input.js"
import "./sg-thumbnail.js"
import { appStore } from "./app-store.js"
import { appActions } from "./app-actions.js"

class SocialGameApp extends HTMLElement {
  constructor() {
    super()
    this.$ = {}
    this._viewportEvents = null
    this._state = {
      imageUrl: "",
      isImageRefreshLoading: false,
    }
  }

  connectedCallback() {
    document.documentElement.setAttribute("data-theme", appStore.getState().theme)

    this.innerHTML = `
      <div class="app-viewport">
        <div class="sg-layout-root">
          <section class="sg-chat-pane" aria-label="Dialogbereich">
            <sg-chat class="sg-chat-component"></sg-chat>
            <sg-input class="sg-input-component"></sg-input>
          </section>
          <section class="sg-scene-image-slot" aria-label="Szenenbild">
            <div class="sg-image-pane">
              <div class="sg-image-empty sg-hidden">Kein Bild geladen</div>
              <sg-thumbnail class="sg-scene-thumbnail"></sg-thumbnail>
            </div>
          </section>
        </div>
      </div>
    `

    this.$ = {
      input: this.querySelector("sg-input"),
      imageSlot: this.querySelector(".sg-scene-image-slot"),
      imageEmpty: this.querySelector(".sg-scene-image-slot .sg-image-empty"),
    }

    appStore.subscribe("focusRequestedAt", this.onInputFocusRequested.bind(this))
    appStore.subscribe("imageUrl", this.onImageUrlChanged.bind(this))
    appStore.subscribe("isImageRefreshLoading", this.onImageRefreshLoadingChanged.bind(this))
    this.syncImageFromStore()
    this.renderSceneImageState()
    this.registerViewportSync()
    this.syncViewportHeight()
    appActions.loadInitialState()
  }

  disconnectedCallback() {
    this._viewportEvents?.abort()
    this._viewportEvents = null
  }

  registerViewportSync() {
    const controller = new AbortController()
    const visualViewport = window.visualViewport

    this._viewportEvents?.abort()
    this._viewportEvents = controller
    window.addEventListener("resize", this.syncViewportHeight.bind(this), { signal: controller.signal })

    if (!visualViewport) {
      return
    }

    visualViewport.addEventListener("resize", this.syncViewportHeight.bind(this), { signal: controller.signal })
    visualViewport.addEventListener("scroll", this.syncViewportHeight.bind(this), { signal: controller.signal })
  }

  syncViewportHeight() {
    const height = Math.max(Math.round(window.visualViewport?.height || window.innerHeight), 1)
    document.documentElement.style.setProperty("--app-vh", `${height}px`)
  }

  focusInput() {
    requestAnimationFrame(() => this.$.input?.focusInput())
  }

  syncImageFromStore() {
    const state = appStore.getState()
    this._state.imageUrl = typeof state.imageUrl === "string" ? state.imageUrl : ""
    this._state.isImageRefreshLoading = Boolean(state.isImageRefreshLoading)
  }

  onImageUrlChanged(imageUrl) {
    this._state.imageUrl = typeof imageUrl === "string" ? imageUrl : ""
    this.renderSceneImageState()
  }

  onImageRefreshLoadingChanged(isImageRefreshLoading) {
    this._state.isImageRefreshLoading = Boolean(isImageRefreshLoading)
    this.renderSceneImageState()
  }

  renderSceneImageState() {
    const hasImage = this._state.imageUrl.trim().length > 0
    const showSlotLoading = Boolean(hasImage && this._state.isImageRefreshLoading)

    this.$.imageEmpty.classList.toggle("sg-hidden", hasImage)
    this.$.imageSlot.classList.toggle("is-loading", showSlotLoading)
  }

  onInputFocusRequested() {
    this.focusInput()
  }
}

customElements.get("sg-app") || customElements.define("sg-app", SocialGameApp)
