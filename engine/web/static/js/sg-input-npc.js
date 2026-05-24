import { appStore } from "./app-store.js"
import { appActions } from "./app-actions.js"
import { PLUS_ICON } from "./icons.js"
import "./sg-reference-image-input.js"
import "./sg-settings-action.js"

class SocialGameInputNpc extends HTMLElement {
  constructor() {
    super()
    this._state = {
      isLoading: false,
      isImageActionLoading: false,
      errorMessage: "",
    }
    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = this.template()
    this.$ = this.cacheElements()
    this.registerEventListeners()
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  template() {
    return /*html*/ `
      <section class="sg-settings-section">
        <h3 class="sg-settings-heading">Neue Figur erstellen</h3>
        <div class="sg-form-group">
          <label for="npc-description-input" class="sg-form-label">Charakterbeschreibung <span class="sg-form-required">*</span></label>
          <p class="sg-form-hint-small">Die Beschreibung wird verwendet, um Name, Charakter, initialen Zustand und Bild der neuen Figur zu erzeugen.</p>
          <textarea id="npc-description-input" class="sg-settings-textarea" placeholder="z. B. Alex ist ein ruhiger Koch Anfang 30, beobachtet genau und spricht selten direkt aus, was er denkt..." required aria-required="true"></textarea>
        </div>

        <sg-reference-image-input preview-alt="Vorschau des NPC-Profilbilds"></sg-reference-image-input>

        <div class="sg-scene-error sg-hidden"></div>

        <sg-settings-action data-action="create-npc" aria-label="NPC erstellen">
          <span slot="icon">${PLUS_ICON}</span>
          <span>NPC erstellen</span>
          <span slot="description">Erzeugt eine neue Figur aus deiner Charakterbeschreibung</span>
        </sg-settings-action>
      </section>
    `
  }

  cacheElements() {
    return {
      characterDescriptionInput: this.querySelector("#npc-description-input"),
      referenceInput: this.querySelector("sg-reference-image-input"),
      submitButton: this.querySelector('[data-action="create-npc"]'),
      errorElement: this.querySelector(".sg-scene-error"),
    }
  }

  registerEventListeners() {
    this.$.characterDescriptionInput.addEventListener("input", this.render.bind(this))
    this.$.referenceInput.addEventListener("referenceChanged", this.handleReferenceChanged.bind(this))
    this.$.referenceInput.addEventListener("referenceRemoved", this.handleReferenceChanged.bind(this))
    this.$.referenceInput.addEventListener("imageError", this.handleImageError.bind(this))
    this.$.referenceInput.addEventListener("describeRequested", this.handleDescribeReference.bind(this))
    this.$.referenceInput.addEventListener("previewRequested", this.handleCreatePreviewImage.bind(this))
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
    if (wasLoading && !this._state.isLoading && !this._state.errorMessage) {
      this.resetDialogState()
      this.dispatchEvent(new CustomEvent("npcCreateFinished", { bubbles: true, composed: true }))
    }
  }

  onNpcCreatorErrorChanged(errorMessage) {
    this._state.errorMessage = typeof errorMessage === "string" ? errorMessage : ""
    this.render()
  }

  handleReferenceChanged() {
    appStore.setState({ npcCreatorError: "" })
    this.render()
  }

  handleImageError(event) {
    appStore.setState({ npcCreatorError: event.detail?.message || "Referenzbild wurde abgelehnt." })
  }

  async handleDescribeReference() {
    if (!this.$.referenceInput.referenceImageDataUrl || this._state.isImageActionLoading) {
      return
    }
    await this.runImageAction(async () => {
      const description = await appActions.describeNpcReference(this.$.referenceInput.referenceImageDataUrl)
      if (description.trim()) {
        this.$.characterDescriptionInput.value = description.trim()
      }
    })
  }

  async handleCreatePreviewImage() {
    const characterDescription = this.$.characterDescriptionInput.value.trim()
    if (!characterDescription || this._state.isImageActionLoading) {
      return
    }
    await this.runImageAction(async () => {
      const imageDataUrl = await appActions.createNpcPreviewImage(characterDescription, this.$.referenceInput.referenceImageDataUrl)
      if (imageDataUrl) {
        this.$.referenceInput.setPreviewImage(imageDataUrl)
      }
    })
  }

  async runImageAction(action) {
    this._state.isImageActionLoading = true
    appStore.setState({ npcCreatorError: "" })
    this.render()
    try {
      await action()
    } catch (error) {
      appStore.setState({ npcCreatorError: error instanceof Error ? error.message : "Bildaktion fehlgeschlagen." })
    } finally {
      this._state.isImageActionLoading = false
      this.render()
    }
  }

  handleSubmit(e) {
    e.preventDefault()
    if (this._state.isLoading || this._state.isImageActionLoading) {
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
      npc_image_data_url: this.$.referenceInput.previewImageDataUrl,
      reference_image_data_url: this.$.referenceInput.referenceImageDataUrl,
    })
  }

  resetDialogState() {
    this.$.characterDescriptionInput.value = ""
    this.$.referenceInput.reset()
    this.render()
  }

  render() {
    const hasDescription = Boolean(this.$.characterDescriptionInput.value.trim())
    const isBusy = this._state.isLoading || this._state.isImageActionLoading
    this.$.submitButton.disabled = isBusy || !hasDescription
    this.$.referenceInput.update({ busy: isBusy, canCreatePreview: hasDescription })
    this.renderError()
    this.$.characterDescriptionInput.disabled = isBusy
  }

  renderError() {
    const errorVisible = Boolean(this._state.errorMessage)
    this.$.errorElement.classList.toggle("sg-hidden", !errorVisible)
    if (errorVisible) {
      this.$.errorElement.textContent = this._state.errorMessage
    }
  }
}

customElements.get("sg-input-npc") || customElements.define("sg-input-npc", SocialGameInputNpc)
