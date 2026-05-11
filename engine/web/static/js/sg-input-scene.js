import { appStore } from "./app-store.js"
import { appActions } from "./app-actions.js"
import "./sg-settings-action.js"

const CREATE_ICON = /*html*/ `
  <svg slot="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <path d="M12 5v14M5 12h14"></path>
  </svg>
`

class SocialGameInputScene extends HTMLElement {
  constructor() {
    super()
    this._state = {
      isLoading: false,
      errorMessage: "",
    }
    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = /*html*/ `
      <section class="sg-settings-section">
        <h3 class="sg-settings-heading">Neue Szene für aktive Figur</h3>
        <div class="sg-form-group">
          <label for="scene-description-input" class="sg-form-label">
            Szenenbeschreibung <span class="sg-form-required">*</span>
          </label>
          <p class="sg-form-hint-small">Die Beschreibung wird für die aktivierten Inhalte verwendet.</p>
          <textarea
            id="scene-description-input"
            class="sg-settings-textarea"
            placeholder="z. B. Ein gemütliches Café mit warmem Licht, der NPC sitzt links am Fenster..."
            required
            aria-required="true"
          ></textarea>
        </div>

        <label class="sg-settings-checkbox">
          <input type="checkbox" data-option="create-scene" checked />
          <span>Scene Erstellen</span>
        </label>
        <label class="sg-settings-checkbox">
          <input type="checkbox" data-option="create-npc-context" checked />
          <span>NPC Kontext erstellen</span>
        </label>

        <div class="sg-scene-error sg-hidden"></div>

        <sg-settings-action
          data-action="create-scene"
          aria-label="Szene erstellen"
        >
            ${CREATE_ICON}
            <span>Szene erstellen</span>
            <span slot="description">Erzeugt Szene und optionalen NPC-Kontext aus der Beschreibung</span>
        </sg-settings-action>
      </section>
    `

    this.$ = {
      sceneDescriptionInput: this.querySelector("#scene-description-input"),
      createSceneCheckbox: this.querySelector('[data-option="create-scene"]'),
      createNpcContextCheckbox: this.querySelector('[data-option="create-npc-context"]'),
      submitButton: this.querySelector('[data-action="create-scene"]'),
      errorElement: this.querySelector(".sg-scene-error"),
    }

    this.registerEventListeners()
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  registerEventListeners() {
    this.$.sceneDescriptionInput.addEventListener("input", this.render.bind(this))
    this.$.createSceneCheckbox.addEventListener("change", this.render.bind(this))
    this.$.createNpcContextCheckbox.addEventListener("change", this.render.bind(this))
    this.$.submitButton.addEventListener("click", this.handleSubmit.bind(this))
  }

  registerSubscriptions() {
    appStore.subscribe("isSceneCreatorLoading", this.onSceneCreatorLoadingChanged.bind(this))
    appStore.subscribe("sceneCreatorError", this.onSceneCreatorErrorChanged.bind(this))
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.isLoading = Boolean(state.isSceneCreatorLoading)
    this._state.errorMessage = typeof state.sceneCreatorError === "string" ? state.sceneCreatorError : ""
  }

  onSceneCreatorLoadingChanged(isLoading) {
    const wasLoading = this._state.isLoading
    this._state.isLoading = Boolean(isLoading)
    this.render()

    const isSuccessfulCompletion = wasLoading && !this._state.isLoading && !this._state.errorMessage
    if (isSuccessfulCompletion) {
      this.$.sceneDescriptionInput.value = ""
      this.render()
      this.dispatchEvent(new CustomEvent("sceneCreateFinished", { bubbles: true, composed: true }))
    }
  }

  onSceneCreatorErrorChanged(errorMessage) {
    this._state.errorMessage = typeof errorMessage === "string" ? errorMessage : ""
    this.render()
  }

  handleSubmit(e) {
    e.preventDefault()

    if (this._state.isLoading) {
      return
    }

    const sceneDescription = this.$.sceneDescriptionInput.value.trim()
    const createScene = this.$.createSceneCheckbox.checked
    const createNpcContext = this.$.createNpcContextCheckbox.checked

    if (!sceneDescription) {
      appStore.setState({ sceneCreatorError: "Szenenbeschreibung ist erforderlich." })
      return
    }
    if (!createScene && !createNpcContext) {
      appStore.setState({ sceneCreatorError: "Mindestens eine Erstellungsoption muss aktiv sein." })
      return
    }

    appStore.setState({ sceneCreatorError: "" })
    appActions.createScene({
      scene_description: sceneDescription,
      create_scene: createScene,
      create_npc_context: createNpcContext,
    })
  }

  render() {
    const hasDescription = Boolean(this.$.sceneDescriptionInput.value.trim())
    const hasCreateOption = this.$.createSceneCheckbox.checked || this.$.createNpcContextCheckbox.checked

    this.$.submitButton.disabled = this._state.isLoading || !hasDescription || !hasCreateOption

    const errorVisible = Boolean(this._state.errorMessage)
    this.$.errorElement.classList.toggle("sg-hidden", !errorVisible)
    if (errorVisible) {
      this.$.errorElement.textContent = this._state.errorMessage
    }

    this.$.sceneDescriptionInput.disabled = this._state.isLoading
    this.$.createSceneCheckbox.disabled = this._state.isLoading
    this.$.createNpcContextCheckbox.disabled = this._state.isLoading
  }
}

customElements.get("sg-input-scene") || customElements.define("sg-input-scene", SocialGameInputScene)
