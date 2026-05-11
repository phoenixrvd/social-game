import { appStore } from "./app-store.js"
import { appActions } from "./app-actions.js"
import "./sg-settings-action.js"

const CREATE_ICON = /*html*/ `
  <svg slot="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <path d="M12 5v14M5 12h14"></path>
  </svg>
`

class SocialGameInputNpc extends HTMLElement {
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
        <h3 class="sg-settings-heading">Neue Figur erstellen</h3>
        <div class="sg-form-group">
          <label for="npc-description-input" class="sg-form-label">
            Charakterbeschreibung <span class="sg-form-required">*</span>
          </label>
          <p class="sg-form-hint-small">Die Beschreibung wird verwendet, um Name, Charakter, initialen Zustand und Bild der neuen Figur zu erzeugen.</p>
          <textarea
            id="npc-description-input"
            class="sg-settings-textarea"
            placeholder="z. B. Alex ist ein ruhiger Koch Anfang 30, beobachtet genau und spricht selten direkt aus, was er denkt..."
            required
            aria-required="true"
          ></textarea>
        </div>

        <div class="sg-scene-error sg-hidden"></div>

        <sg-settings-action
          data-action="create-npc"
          aria-label="NPC erstellen"
        >
            ${CREATE_ICON}
            <span>NPC erstellen</span>
            <span slot="description">Erzeugt eine neue Figur aus deiner Charakterbeschreibung</span>
        </sg-settings-action>
      </section>
    `

    this.$ = {
      characterDescriptionInput: this.querySelector("#npc-description-input"),
      submitButton: this.querySelector('[data-action="create-npc"]'),
      errorElement: this.querySelector(".sg-scene-error"),
    }

    this.registerEventListeners()
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  registerEventListeners() {
    this.$.submitButton.addEventListener("click", this.handleSubmit.bind(this))
  }

  registerSubscriptions() {
    appStore.subscribe("isNpcCreatorLoading", this.onNpcCreatorLoadingChanged.bind(this))
    appStore.subscribe("npcCreatorError", this.onNpcCreatorErrorChanged.bind(this))
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.isLoading = Boolean(state.isNpcCreatorLoading)
    this._state.errorMessage = typeof state.npcCreatorError === "string" ? state.npcCreatorError : ""
  }

  onNpcCreatorLoadingChanged(isLoading) {
    const wasLoading = this._state.isLoading
    this._state.isLoading = Boolean(isLoading)
    this.render()

    const isSuccessfulCompletion = wasLoading && !this._state.isLoading && !this._state.errorMessage
    if (isSuccessfulCompletion) {
      this.$.characterDescriptionInput.value = ""
      this.dispatchEvent(new CustomEvent("npcCreateFinished", { bubbles: true, composed: true }))
    }
  }

  onNpcCreatorErrorChanged(errorMessage) {
    this._state.errorMessage = typeof errorMessage === "string" ? errorMessage : ""
    this.render()
  }

  handleSubmit(e) {
    e.preventDefault()

    if (this._state.isLoading) {
      return
    }

    const characterDescription = this.$.characterDescriptionInput.value.trim()

    if (!characterDescription) {
      appStore.setState({ npcCreatorError: "Charakterbeschreibung ist erforderlich." })
      return
    }

    appStore.setState({ npcCreatorError: "" })
    appActions.createNpc({
      character_description: characterDescription,
    })
  }

  render() {
    this.$.submitButton.disabled = this._state.isLoading

    const errorVisible = Boolean(this._state.errorMessage)
    this.$.errorElement.classList.toggle("sg-hidden", !errorVisible)
    if (errorVisible) {
      this.$.errorElement.textContent = this._state.errorMessage
    }

    this.$.characterDescriptionInput.disabled = this._state.isLoading
  }
}

customElements.get("sg-input-npc") || customElements.define("sg-input-npc", SocialGameInputNpc)
