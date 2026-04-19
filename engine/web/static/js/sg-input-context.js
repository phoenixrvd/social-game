import { appStore } from "./app-store.js"
import "./sg-npc-gallery.js"
import "./sg-scene-gallery.js"

class SocialGameInputContext extends HTMLElement {
  constructor() {
    super()
    this._state = {
      scenes: [],
      sceneId: "",
      disabled: false,
    }

    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = `
      <section class="sg-settings-section">
        <div class="sg-session-row">
          <sg-npc-gallery></sg-npc-gallery>
          <sg-scene-gallery></sg-scene-gallery>
        </div>
      </section>
    `

    this.registerSubscriptions()
    this.syncFromStore()
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.scenes = Array.isArray(state.scenes) ? state.scenes : []
    this._state.sceneId = typeof state.sceneId === "string" ? state.sceneId : ""
    this._state.disabled = Boolean(state.isSending) || Boolean(state.isSessionLoading)
  }

  registerSubscriptions() {
    const subscriptions = [
      ["scenes", this.onScenesChanged.bind(this)],
      ["sceneId", this.onSceneIdChanged.bind(this)],
      ["isSending", this.onDisabledTriggerChanged.bind(this)],
      ["isSessionLoading", this.onDisabledTriggerChanged.bind(this)],
    ]

    for (const [key, listener] of subscriptions) {
      appStore.subscribe(key, listener)
    }
  }

  onScenesChanged(scenes) {
    this._state.scenes = Array.isArray(scenes) ? scenes : []
  }

  onSceneIdChanged(sceneId) {
    this._state.sceneId = typeof sceneId === "string" ? sceneId : ""
  }

  onDisabledTriggerChanged() {
    const state = appStore.getState()
    this._state.disabled = Boolean(state.isSending) || Boolean(state.isSessionLoading)
  }
}

customElements.get("sg-input-context") || customElements.define("sg-input-context", SocialGameInputContext)






