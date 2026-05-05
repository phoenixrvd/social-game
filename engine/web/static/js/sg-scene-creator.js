import { appStore } from "./app-store.js"
import { appActions } from "./app-actions.js"

class SocialGameSceneCreator extends HTMLElement {
  constructor() {
    super()
    this._state = {
      isOpen: false,
      isLoading: false,
      errorMessage: "",
      sceneDescription: "",
      npcSceneDescription: "",
    }
    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = /*html*/ `
      <div class="sg-scene-creator-overlay sg-hidden" role="presentation">
        <div class="sg-scene-creator-modal">
          <div class="sg-scene-creator-header">
            <h2 class="sg-scene-creator-title">Neue Szene erstellen</h2>
            <button
              type="button"
              class="sg-scene-creator-close"
              aria-label="Schließen"
              title="Schließen (ESC)"
            >
              ✕
            </button>
          </div>

          <form class="sg-scene-creator-form" novalidate>
            <div class="sg-form-group">
              <label for="scene-description-input" class="sg-form-label">
                Szenenbeschreibung <span class="sg-form-required">*</span>
              </label>
              <p class="sg-form-hint">Beschreiben Sie die Szene, die Sie erstellen möchten (z.B. "Ein ruhiger Park am Abend")</p>
              <textarea
                id="scene-description-input"
                class="sg-form-textarea"
                placeholder="z.B. Ein gemütliches Café mit warmem Licht..."
                required
                aria-required="true"
              ></textarea>
            </div>

            <div class="sg-form-group">
              <label for="npc-scene-description-input" class="sg-form-label">
                NPC-spezifische Szenenbeschreibung
              </label>
              <p class="sg-form-hint">Optional: Beschreiben Sie, wie der NPC diese Szene wahrnimmt und erlebt</p>
              <textarea
                id="npc-scene-description-input"
                class="sg-form-textarea"
                placeholder="z.B. Sie sitzt in ihrer Lieblingsecke..."
              ></textarea>
            </div>

            <div class="sg-scene-creator-error sg-hidden"></div>

            <div class="sg-scene-creator-actions">
              <button
                type="submit"
                class="sg-scene-creator-submit"
                aria-label="Szene erstellen"
              >
                Szene erstellen
              </button>
            </div>
          </form>
        </div>
      </div>
    `

    this.$ = {
      overlay: this.querySelector(".sg-scene-creator-overlay"),
      modal: this.querySelector(".sg-scene-creator-modal"),
      form: this.querySelector(".sg-scene-creator-form"),
      sceneDescriptionInput: this.querySelector("#scene-description-input"),
      npcSceneDescriptionInput: this.querySelector("#npc-scene-description-input"),
      closeButton: this.querySelector(".sg-scene-creator-close"),
      submitButton: this.querySelector(".sg-scene-creator-submit"),
      errorElement: this.querySelector(".sg-scene-creator-error"),
    }

    this.registerEventListeners()
    this.registerSubscriptions()
    this.syncFromStore()
  }

  registerEventListeners() {
    this.$.closeButton.addEventListener("click", () => appActions.closeSceneCreator())
    this.$.form.addEventListener("submit", (e) => this.handleSubmit(e))
    this.$.overlay.addEventListener("click", (e) => {
      if (e.target === this.$.overlay) {
        appActions.closeSceneCreator()
      }
    })
  }

  registerSubscriptions() {
    appStore.subscribe("isSceneCreatorOpen", this.onSceneCreatorOpenChanged.bind(this))
    appStore.subscribe("isSceneCreatorLoading", this.onSceneCreatorLoadingChanged.bind(this))
    appStore.subscribe("sceneCreatorError", this.onSceneCreatorErrorChanged.bind(this))
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.isOpen = Boolean(state.isSceneCreatorOpen)
    this._state.isLoading = Boolean(state.isSceneCreatorLoading)
    this._state.errorMessage = typeof state.sceneCreatorError === "string" ? state.sceneCreatorError : ""
  }

  onSceneCreatorOpenChanged(isOpen) {
    this._state.isOpen = Boolean(isOpen)
    this.render()
  }

  onSceneCreatorLoadingChanged(isLoading) {
    this._state.isLoading = Boolean(isLoading)
    this.render()
  }

  onSceneCreatorErrorChanged(errorMessage) {
    this._state.errorMessage = typeof errorMessage === "string" ? errorMessage : ""
    this.render()
  }

  async handleSubmit(e) {
    e.preventDefault()

    if (this._state.isLoading) {
      return
    }

    const sceneDescription = this.$.sceneDescriptionInput.value.trim()
    const npcSceneDescription = this.$.npcSceneDescriptionInput.value.trim()

    if (!sceneDescription) {
      appStore.setState({ sceneCreatorError: "Szenenbeschreibung ist erforderlich." })
      return
    }

    appActions.createScene({
      scene_description: sceneDescription,
      npc_scene_description: npcSceneDescription,
    })
  }

  render() {
    const isVisible = this._state.isOpen
    this.$.overlay.classList.toggle("sg-hidden", !isVisible)

    if (isVisible) {
      requestAnimationFrame(() => {
        this.$.overlay.focus()
        this.$.sceneDescriptionInput.focus()
      })
    }

    this.$.submitButton.disabled = this._state.isLoading
    this.$.form.classList.toggle("sg-scene-creator-form--loading", this._state.isLoading)

    const errorVisible = Boolean(this._state.errorMessage)
    this.$.errorElement.classList.toggle("sg-hidden", !errorVisible)
    if (errorVisible) {
      this.$.errorElement.textContent = this._state.errorMessage
    }

    if (this._state.isOpen && !this._state.isLoading) {
      this.$.sceneDescriptionInput.value = this._state.sceneDescription
      this.$.npcSceneDescriptionInput.value = this._state.npcSceneDescription
    }

    if (!isVisible) {
      this._state.sceneDescription = ""
      this._state.npcSceneDescription = ""
    }
  }
}

customElements.get("sg-scene-creator") ||
  customElements.define("sg-scene-creator", SocialGameSceneCreator)
