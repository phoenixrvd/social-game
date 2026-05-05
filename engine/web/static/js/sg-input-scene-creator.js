import { appStore } from "./app-store.js"
import { appActions } from "./app-actions.js"

class SocialGameInputSceneCreator extends HTMLElement {
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
      <div class="sg-form-group">
        <label for="scene-description-creator-input" class="sg-form-label">
          Szenenbeschreibung <span class="sg-form-required">*</span>
        </label>
        <p class="sg-form-hint-small">Beschreiben Sie die Szene, die Sie erstellen möchten</p>
        <textarea
          id="scene-description-creator-input"
          class="sg-settings-textarea"
          placeholder="z.B. Ein gemütliches Café mit warmem Licht..."
          required
          aria-required="true"
        ></textarea>
      </div>

      <div class="sg-scene-creator-error sg-hidden"></div>

      <button
        type="button"
        class="sg-settings-action sg-scene-create-action"
        aria-label="Szene erstellen"
      >
        Szene erstellen
      </button>
    `

    this.$ = {
      sceneDescriptionInput: this.querySelector("#scene-description-creator-input"),
      submitButton: this.querySelector(".sg-scene-create-action"),
      errorElement: this.querySelector(".sg-scene-creator-error"),
    }

    this.registerEventListeners()
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  registerEventListeners() {
    this.$.submitButton.addEventListener("click", (e) => this.handleSubmit(e))
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

    if (!sceneDescription) {
      appStore.setState({ sceneCreatorError: "Szenenbeschreibung ist erforderlich." })
      return
    }

    appStore.setState({ sceneCreatorError: "" })
    appActions.createScene({
      scene_description: sceneDescription,
    })
  }

  render() {
    this.$.submitButton.disabled = this._state.isLoading

    const errorVisible = Boolean(this._state.errorMessage)
    this.$.errorElement.classList.toggle("sg-hidden", !errorVisible)
    if (errorVisible) {
      this.$.errorElement.textContent = this._state.errorMessage
    }

    this.$.sceneDescriptionInput.disabled = this._state.isLoading
  }

}

customElements.get("sg-input-scene-creator") ||
  customElements.define("sg-input-scene-creator", SocialGameInputSceneCreator)









