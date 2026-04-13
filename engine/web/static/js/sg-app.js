import "./sg-chat.js"
import "./sg-input.js"
import "./sg-scene-image.js"
import { appStore } from "./app-store.js"
import { appActions } from "./app-actions.js"

class SocialGameApp extends HTMLElement {
  constructor() {
    super()
    this.$ = {}
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
    appActions.loadInitialState()
  }

  focusInput() {
    requestAnimationFrame(() => this.$.input?.focusInput())
  }

  onInputFocusRequested() {
    this.focusInput()
  }
}

customElements.get("sg-app") || customElements.define("sg-app", SocialGameApp)
