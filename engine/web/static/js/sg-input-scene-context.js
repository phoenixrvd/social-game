import { appStore } from "./app-store.js"
import { appActions } from "./app-actions.js"
import { SAVE_ICON, TEXT_ICON } from "./icons.js"
import "./sg-settings-action.js"

const SCENE_CONTEXT_TEMPLATE = /*html*/ `
  <section class="sg-settings-section">
    <h3 class="sg-settings-heading">Scene Context bearbeiten</h3>
    <div class="sg-form-group">
      <label for="scene-context-input" class="sg-form-label">
        Scene Context <span class="sg-form-required">*</span>
      </label>
      <p class="sg-form-hint-small">Beschreibe, wie der NPC in der Szene erscheint: z. B. wo er steht, wohin er schaut oder wie er angekleidet ist.</p>
      <textarea id="scene-context-input" class="sg-settings-textarea" aria-label="Scene Context editieren"></textarea>
    </div>

    <div class="sg-scene-error sg-hidden"></div>

    <div class="sg-settings-actions">
      <sg-settings-action data-action="generate-scene-context" aria-label="Neuen Kontext aus Eingabe generieren">
        <span slot="icon">${TEXT_ICON}</span>
        <span>Neuen Kontext aus Eingabe generieren</span>
        <span slot="description">Formt den Text zu einem neuen Kontext um</span>
      </sg-settings-action>
      <sg-settings-action data-action="save-scene-context" aria-label="Kontext speichern">
        <span slot="icon">${SAVE_ICON}</span>
        <span>Kontext speichern</span>
        <span slot="description">Übernimmt den Kontext für die aktive Szene</span>
      </sg-settings-action>
    </div>
  </section>
`

class SocialGameInputSceneContext extends HTMLElement {
  constructor() {
    super()
    this._state = {
      sceneContext: "",
      isLoading: false,
      errorMessage: "",
    }
    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = SCENE_CONTEXT_TEMPLATE
    this.$ = {
      input: this.querySelector("#scene-context-input"),
      generateButton: this.querySelector('[data-action="generate-scene-context"]'),
      saveButton: this.querySelector('[data-action="save-scene-context"]'),
      errorElement: this.querySelector(".sg-scene-error"),
    }

    this.$.input.addEventListener("input", this.onInputChanged.bind(this))
    this.$.generateButton.addEventListener("click", this.onGenerateClicked.bind(this))
    this.$.saveButton.addEventListener("click", this.onSaveClicked.bind(this))
    this.registerSubscriptions()
    this.syncFromStore()
    this.prepare()
  }

  registerSubscriptions() {
    appStore.subscribe("sceneContext", this.onSceneContextChanged.bind(this))
    appStore.subscribe("isSceneContextLoading", this.onSceneContextLoadingChanged.bind(this))
    appStore.subscribe("sceneContextError", this.onSceneContextErrorChanged.bind(this))
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.sceneContext = typeof state.sceneContext === "string" ? state.sceneContext : ""
    this._state.isLoading = Boolean(state.isSceneContextLoading)
    this._state.errorMessage = typeof state.sceneContextError === "string" ? state.sceneContextError : ""
  }

  prepare() {
    this.$.input.value = this._state.sceneContext
    appStore.setState({ sceneContextError: "" })
    this.render()
  }

  onSceneContextChanged(sceneContext) {
    this._state.sceneContext = typeof sceneContext === "string" ? sceneContext : ""
    if (!this._state.isLoading) {
      this.$.input.value = this._state.sceneContext
    }
    this.render()
  }

  onSceneContextLoadingChanged(isLoading) {
    this._state.isLoading = Boolean(isLoading)
    this.render()
  }

  onSceneContextErrorChanged(errorMessage) {
    this._state.errorMessage = typeof errorMessage === "string" ? errorMessage : ""
    this.render()
  }

  onInputChanged() {
    if (this._state.errorMessage) {
      appStore.setState({ sceneContextError: "" })
    }
    this.render()
  }

  async onGenerateClicked(event) {
    event.preventDefault()
    if (this._state.isLoading || !this.$.input.value.trim()) {
      return
    }
    const generatedContext = await appActions.generateSceneContext(this.$.input.value)
    if (generatedContext !== null) {
      this.$.input.value = generatedContext
    }
    this.render()
  }

  async onSaveClicked(event) {
    event.preventDefault()
    if (this._state.isLoading) {
      return
    }
    await appActions.updateSceneContext(this.$.input.value)
  }

  render() {
    const canGenerate = Boolean(this.$.input.value.trim())
    this.$.input.disabled = this._state.isLoading
    this.$.generateButton.disabled = this._state.isLoading || !canGenerate
    this.$.saveButton.disabled = this._state.isLoading

    const errorVisible = Boolean(this._state.errorMessage)
    this.$.errorElement.classList.toggle("sg-hidden", !errorVisible)
    if (errorVisible) {
      this.$.errorElement.textContent = this._state.errorMessage
    }
  }
}

customElements.get("sg-input-scene-context") || customElements.define("sg-input-scene-context", SocialGameInputSceneContext)
