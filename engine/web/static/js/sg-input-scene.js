import { appStore } from "./app-store.js"
import { appActions } from "./app-actions.js"
import { PLUS_ICON } from "./icons.js"
import "./sg-reference-image-input.js"
import "./sg-settings-action.js"

const SCENE_TEMPLATE = /*html*/ `
  <section class="sg-settings-section">
    <h3 class="sg-settings-heading">Neue Szene für aktive Figur</h3>
    <div class="sg-form-group">
      <label for="scene-description-input" class="sg-form-label">
        Szenenbeschreibung <span class="sg-form-required">*</span>
      </label>
      <p class="sg-form-hint-small">Die Beschreibung wird für die neue Szene und den NPC-Kontext verwendet.</p>
      <textarea id="scene-description-input" class="sg-settings-textarea" placeholder="z. B. Ein gemütliches Café mit warmem Licht, der NPC sitzt links am Fenster..." required aria-required="true"></textarea>
    </div>

    <sg-reference-image-input preview-alt="Vorschau des Szenenbilds"></sg-reference-image-input>

    <div class="sg-scene-error sg-hidden"></div>

    <sg-settings-action data-action="create-scene" aria-label="Szene erstellen">
        <span slot="icon">${PLUS_ICON}</span>
        <span>Szene erstellen</span>
        <span slot="description">Erzeugt Szene und NPC-Kontext aus der Beschreibung</span>
    </sg-settings-action>
  </section>
`

class SocialGameInputScene extends HTMLElement {
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
    this.innerHTML = SCENE_TEMPLATE
    this.$ = this.cacheElements()

    this.registerEventListeners()
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  cacheElements() {
    return {
      sceneDescriptionInput: this.querySelector("#scene-description-input"),
      referenceInput: this.querySelector("sg-reference-image-input"),
      submitButton: this.querySelector('[data-action="create-scene"]'),
      errorElement: this.querySelector(".sg-scene-error"),
    }
  }

  registerEventListeners() {
    this.$.sceneDescriptionInput.addEventListener("input", this.render.bind(this))
    this.$.referenceInput.addEventListener("referenceChanged", this.handleReferenceChanged.bind(this))
    this.$.referenceInput.addEventListener("imageError", this.handleImageError.bind(this))
    this.$.referenceInput.addEventListener("describeRequested", this.handleDescribeReference.bind(this))
    this.$.referenceInput.addEventListener("previewRequested", this.handleCreatePreviewImage.bind(this))
    this.$.referenceInput.addEventListener("referenceRemoved", this.handleReferenceChanged.bind(this))
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

    if (wasLoading && !this._state.isLoading && !this._state.errorMessage) {
      this.resetDialogState()
      this.dispatchEvent(new CustomEvent("sceneCreateFinished", { bubbles: true, composed: true }))
    }
  }

  onSceneCreatorErrorChanged(errorMessage) {
    this._state.errorMessage = typeof errorMessage === "string" ? errorMessage : ""
    this.render()
  }

  handleReferenceChanged() {
    appStore.setState({ sceneCreatorError: "" })
    this.render()
  }

  handleImageError(event) {
    appStore.setState({ sceneCreatorError: event.detail?.message || "Referenzbild wurde abgelehnt." })
  }

  async handleDescribeReference() {
    if (!this.$.referenceInput.referenceImageDataUrl || this._state.isImageActionLoading) {
      return
    }
    await this.runImageAction(async () => {
      const description = await appActions.describeSceneReference(this.$.referenceInput.referenceImageDataUrl)
      if (description.trim()) {
        this.$.sceneDescriptionInput.value = description.trim()
      }
    })
  }

  async handleCreatePreviewImage() {
    const sceneDescription = this.$.sceneDescriptionInput.value.trim()
    if (!sceneDescription || this._state.isImageActionLoading) {
      return
    }
    await this.runImageAction(async () => {
      const imageDataUrl = await appActions.createScenePreviewImage(sceneDescription, this.$.referenceInput.referenceImageDataUrl)
      if (imageDataUrl) {
        this.$.referenceInput.setPreviewImage(imageDataUrl)
      }
    })
  }

  async runImageAction(action) {
    this._state.isImageActionLoading = true
    appStore.setState({ sceneCreatorError: "" })
    this.render()
    try {
      await action()
    } catch (error) {
      appStore.setState({ sceneCreatorError: error instanceof Error ? error.message : "Bildaktion fehlgeschlagen." })
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

    const sceneDescription = this.$.sceneDescriptionInput.value.trim()

    if (!sceneDescription) {
      appStore.setState({ sceneCreatorError: "Szenenbeschreibung ist erforderlich." })
      return
    }

    appStore.setState({ sceneCreatorError: "" })
    appActions.createScene({
      scene_description: sceneDescription,
      scene_image_data_url: this.$.referenceInput.previewImageDataUrl,
      reference_image_data_url: this.$.referenceInput.referenceImageDataUrl,
    })
  }

  resetDialogState() {
    this.$.sceneDescriptionInput.value = ""
    this.$.referenceInput.reset()
    this.render()
  }

  render() {
    const hasDescription = Boolean(this.$.sceneDescriptionInput.value.trim())
    const isBusy = this._state.isLoading || this._state.isImageActionLoading

    this.$.submitButton.disabled = isBusy || !hasDescription
    this.$.referenceInput.update({ busy: isBusy, canCreatePreview: hasDescription })

    const errorVisible = Boolean(this._state.errorMessage)
    this.$.errorElement.classList.toggle("sg-hidden", !errorVisible)
    if (errorVisible) {
      this.$.errorElement.textContent = this._state.errorMessage
    }

    this.$.sceneDescriptionInput.disabled = isBusy
  }

}

customElements.get("sg-input-scene") || customElements.define("sg-input-scene", SocialGameInputScene)
