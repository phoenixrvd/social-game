import "./sg-chat.js"
import "./sg-input.js"
import "./sg-scene-image.js"
import { appStore } from "./app-store.js"
import { appActions } from "./app-actions.js"

class SocialGameApp extends HTMLElement {
  constructor() {
    super()
    this.$ = {}
    this._viewportEvents = null
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
            <sg-scene-image></sg-scene-image>
          </section>
        </div>
      </div>
    `

    this.$ = {
      input: this.querySelector("sg-input"),
    }

    appStore.subscribe("focusRequestedAt", this.onInputFocusRequested.bind(this))
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

  onInputFocusRequested() {
    this.focusInput()
  }
}

customElements.get("sg-app") || customElements.define("sg-app", SocialGameApp)
