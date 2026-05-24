import { DELETE_ICON, IMAGE_ICON, TEXT_ICON } from "./icons.js"
import "./sg-settings-action.js"

const MAX_REFERENCE_EDGE = 1536
const MAX_REFERENCE_BYTES = 5 * 1024 * 1024

function isSupportedImage(file) {
  return ["image/png", "image/jpeg", "image/webp"].includes(file.type)
}

function loadImage(dataUrl) {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error("Bilddatei konnte nicht dekodiert werden."))
    image.src = dataUrl
  })
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ""))
    reader.onerror = () => reject(new Error("Bilddatei konnte nicht gelesen werden."))
    reader.readAsDataURL(file)
  })
}

function dataUrlBytes(dataUrl) {
  const base64Payload = dataUrl.split(",")[1] || ""
  return Math.ceil((base64Payload.length * 3) / 4)
}

async function resizeReferenceImage(file) {
  if (!isSupportedImage(file)) {
    throw new Error("Nur PNG, JPEG oder WebP sind erlaubt.")
  }
  const image = await loadImage(await readFileAsDataUrl(file))
  const scale = Math.min(1, MAX_REFERENCE_EDGE / image.width, MAX_REFERENCE_EDGE / image.height)
  const canvas = document.createElement("canvas")
  canvas.width = Math.max(1, Math.round(image.width * scale))
  canvas.height = Math.max(1, Math.round(image.height * scale))
  const context = canvas.getContext("2d")
  if (!context) {
    throw new Error("Bild konnte nicht verarbeitet werden.")
  }
  context.drawImage(image, 0, 0, canvas.width, canvas.height)
  return encodeReferenceImage(canvas)
}

function encodeReferenceImage(canvas) {
  for (const quality of [0.9, 0.82, 0.74, 0.66]) {
    const dataUrl = canvas.toDataURL("image/webp", quality)
    if (dataUrlBytes(dataUrl) <= MAX_REFERENCE_BYTES) {
      return dataUrl
    }
  }
  throw new Error("Das verkleinerte Referenzbild ist groesser als 5 MB.")
}

class SocialGameReferenceImageInput extends HTMLElement {
  constructor() {
    super()
    this._state = { busy: false, canCreatePreview: false, referenceImageDataUrl: null, previewImageDataUrl: null }
    this.$ = {}
    this._lastFocusedElement = null
  }

  connectedCallback() {
    this.innerHTML = this.template()
    this.$ = this.cacheElements()
    this.registerEventListeners()
    this.render()
  }

  template() {
    const previewAlt = this.getAttribute("preview-alt") || "Bildvorschau"
    return /*html*/ `
      <div class="sg-scene-reference-panel">
        <div class="sg-scene-preview" data-empty="true" role="button" tabindex="0" aria-label="Referenzbild wählen">
          <input type="file" accept="image/png,image/jpeg,image/webp" hidden />
          <span class="sg-image-content">
            <img class="sg-image-bg sg-hidden" alt="" aria-hidden="true" />
            <img class="sg-image-main sg-hidden" alt="${previewAlt}" />
          </span>
          <span class="sg-scene-preview-placeholder">Bild auswählen</span>
        </div>
        <div class="sg-image-overlay" role="dialog" aria-modal="true" aria-label="Vergroesserte Bildvorschau" tabindex="-1">
          <div class="sg-image-overlay-frame">
            <img class="sg-image-overlay-bg" src="data:," alt="" aria-hidden="true" loading="lazy" decoding="async" />
            <img class="sg-image-overlay-main" src="data:," alt="${previewAlt}" loading="lazy" decoding="async" />
          </div>
        </div>
        <div class="sg-scene-reference-actions">
          <sg-settings-action data-action="describe-reference" aria-label="Beschreibung aus Bild" compact>
            <span slot="icon">${TEXT_ICON}</span>
            <span>Beschreibung aus Bild</span>
          </sg-settings-action>
          <sg-settings-action data-action="preview-image" aria-label="Bild aus Beschreibung" compact>
            <span slot="icon">${IMAGE_ICON}</span>
            <span>Bild aus Beschreibung</span>
          </sg-settings-action>
          <sg-settings-action data-action="remove-reference" aria-label="Referenzbild entfernen" compact danger>
            <span slot="icon">${DELETE_ICON}</span>
            <span>Bild löschen</span>
          </sg-settings-action>
          <slot></slot>
        </div>
      </div>
    `
  }

  cacheElements() {
    return {
      input: this.querySelector('input[type="file"]'),
      preview: this.querySelector(".sg-scene-preview"),
      previewBg: this.querySelector(".sg-image-bg"),
      previewImage: this.querySelector(".sg-image-main"),
      placeholder: this.querySelector(".sg-scene-preview-placeholder"),
      overlay: this.querySelector(".sg-image-overlay"),
      overlayBg: this.querySelector(".sg-image-overlay-bg"),
      overlayMain: this.querySelector(".sg-image-overlay-main"),
      describeButton: this.querySelector('[data-action="describe-reference"]'),
      previewButton: this.querySelector('[data-action="preview-image"]'),
      removeButton: this.querySelector('[data-action="remove-reference"]'),
    }
  }

  registerEventListeners() {
    this.$.input.addEventListener("change", this.handleReferenceSelected.bind(this))
    this.$.preview.addEventListener("click", this.handlePreviewAreaClick.bind(this))
    this.$.preview.addEventListener("keydown", this.handlePreviewAreaKeyDown.bind(this))
    this.$.overlay.addEventListener("click", this.handleOverlayClick.bind(this))
    this.$.overlay.addEventListener("keydown", this.handleOverlayKeyDown.bind(this))
    this.$.describeButton.addEventListener("click", this.handleDescribeClick.bind(this))
    this.$.previewButton.addEventListener("click", this.handlePreviewClick.bind(this))
    this.$.removeButton.addEventListener("click", this.handleRemoveClick.bind(this))
  }

  async handleReferenceSelected() {
    const file = this.$.input.files[0]
    if (!file) {
      return
    }
    try {
      this._state.referenceImageDataUrl = await resizeReferenceImage(file)
      this._state.previewImageDataUrl = null
      this.dispatchEvent(new CustomEvent("referenceChanged", { detail: { imageDataUrl: this._state.referenceImageDataUrl } }))
    } catch (error) {
      const message = error instanceof Error ? error.message : "Referenzbild wurde abgelehnt."
      this.dispatchEvent(new CustomEvent("imageError", { detail: { message } }))
    } finally {
      this.$.input.value = ""
      this.render()
    }
  }

  handleDescribeClick() {
    if (!this._state.busy && this._state.referenceImageDataUrl) {
      this.dispatchEvent(new CustomEvent("describeRequested"))
    }
  }

  handlePreviewClick() {
    if (!this._state.busy && this._state.canCreatePreview) {
      this.dispatchEvent(new CustomEvent("previewRequested"))
    }
  }

  handlePreviewAreaClick() {
    this.openPreviewTarget()
  }

  handlePreviewAreaKeyDown(event) {
    if (event.key !== "Enter" && event.key !== " ") {
      return
    }
    event.preventDefault()
    this.openPreviewTarget()
  }

  openPreviewTarget() {
    if (this._state.busy) {
      return
    }
    if (this._state.previewImageDataUrl) {
      this.openOverlay()
      return
    }
    this.$.input.click()
  }

  openOverlay() {
    this._lastFocusedElement = document.activeElement
    this.$.overlay.classList.add("is-open")
    this.$.overlay.focus()
  }

  handleOverlayClick() {
    this.closeOverlay()
  }

  handleOverlayKeyDown(event) {
    if (event.key === "Escape") {
      event.preventDefault()
      this.closeOverlay()
    }
  }

  closeOverlay() {
    const wasOpen = this.$.overlay.classList.contains("is-open")
    this.$.overlay.classList.remove("is-open")
    if (wasOpen && this._lastFocusedElement instanceof HTMLElement) {
      this._lastFocusedElement.focus()
    }
    this._lastFocusedElement = null
  }

  handleRemoveClick() {
    if (this._state.busy || !this.visibleImageDataUrl) {
      return
    }
    this._state.referenceImageDataUrl = null
    this._state.previewImageDataUrl = null
    this.dispatchEvent(new CustomEvent("referenceRemoved"))
    this.render()
  }

  update({ busy, canCreatePreview }) {
    this._state.busy = Boolean(busy)
    this._state.canCreatePreview = Boolean(canCreatePreview)
    this.render()
  }

  setPreviewImage(imageDataUrl) {
    this._state.previewImageDataUrl = typeof imageDataUrl === "string" && imageDataUrl ? imageDataUrl : null
    this.render()
  }

  reset() {
    this._state.referenceImageDataUrl = null
    this._state.previewImageDataUrl = null
    this.render()
  }

  get referenceImageDataUrl() {
    return this._state.referenceImageDataUrl
  }

  get visibleImageDataUrl() {
    return this._state.previewImageDataUrl || this._state.referenceImageDataUrl
  }

  get previewImageDataUrl() {
    return this._state.previewImageDataUrl
  }

  render() {
    const imageDataUrl = this.visibleImageDataUrl
    this.$.input.disabled = this._state.busy
    this.$.describeButton.disabled = this._state.busy || !this._state.referenceImageDataUrl
    this.$.previewButton.disabled = this._state.busy || !this._state.canCreatePreview
    this.$.removeButton.disabled = this._state.busy || !imageDataUrl
    this.renderPreview(imageDataUrl)
  }

  renderPreview(imageDataUrl) {
    const hasPreview = Boolean(imageDataUrl)
    const hasGeneratedPreview = Boolean(this._state.previewImageDataUrl)
    this.$.preview.dataset.empty = hasPreview ? "false" : "true"
    this.$.preview.setAttribute("aria-label", hasGeneratedPreview ? "Bildvorschau vergroessern" : "Referenzbild wählen")
    this.$.previewImage.classList.toggle("sg-hidden", !hasPreview)
    this.$.previewBg.classList.toggle("sg-hidden", !hasPreview)
    this.$.placeholder.classList.toggle("sg-hidden", hasPreview)
    if (hasPreview) {
      this.$.previewImage.src = imageDataUrl
      this.$.previewBg.src = imageDataUrl
    } else {
      this.$.previewImage.removeAttribute("src")
      this.$.previewBg.removeAttribute("src")
    }
    this.renderOverlay()
  }

  renderOverlay() {
    if (this._state.previewImageDataUrl) {
      this.$.overlayBg.src = this._state.previewImageDataUrl
      this.$.overlayMain.src = this._state.previewImageDataUrl
    } else {
      this.closeOverlay()
      this.$.overlayBg.src = "data:,"
      this.$.overlayMain.src = "data:,"
    }
  }
}

customElements.get("sg-reference-image-input") || customElements.define("sg-reference-image-input", SocialGameReferenceImageInput)
