import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"

const REFRESH_ICON = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <path d="M3 3h18v18H3z"></path>
    <path d="M3 15l5-5 4 4 3-3 6 6"></path>
    <path d="M16 8h4v4"></path>
    <path d="M20 8l-4 4"></path>
  </svg>
`

const REVERT_ICON = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <path d="M21 12a9 9 0 1 1-3.1-6.8"></path>
    <path d="M21 3v6h-6"></path>
  </svg>
`

const DELETE_ICON = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <polyline points="3 6 5 6 21 6"></polyline>
    <path d="M19 6l-1 14H6L5 6"></path>
    <path d="M10 11v6"></path>
    <path d="M14 11v6"></path>
    <path d="M9 6V4h6v2"></path>
  </svg>
`

function renderActionContent(icon, title, description = "") {
  const descriptionMarkup = description ? `<span class="sg-settings-action-text">${description}</span>` : ""
  return `
    <span class="sg-settings-action-icon" aria-hidden="true">${icon}</span>
    <span class="sg-settings-action-copy">
      <span class="sg-settings-action-title">${title}</span>
      ${descriptionMarkup}
    </span>
  `
}

class SocialGameInputImage extends HTMLElement {
  constructor() {
    super()
    this._state = {
      disabled: false,
    }

    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = `
      <section class="sg-settings-section">
        <h3 class="sg-settings-heading">Bild</h3>
        <div class="sg-settings-actions">
          <button type="button" data-action="refresh-image" class="sg-settings-action" aria-label="Bild neu generieren">
            ${renderActionContent(REFRESH_ICON, "Bild neu generieren", "Erzeugt eine neue Variante aus dem aktuellen Kontext")}
          </button>
          <button type="button" data-action="revert-image" class="sg-settings-action" aria-label="Auf letzte Version zurücksetzen">
            ${renderActionContent(REVERT_ICON, "Auf letzte Version zurücksetzen", "Stellt vorheriges Bild wieder her")}
          </button>
          <button type="button" data-action="delete-image" class="sg-settings-action sg-settings-action-danger" aria-label="Bild zurücksetzen">
            ${renderActionContent(DELETE_ICON, "Bild zurücksetzen", "Setzt das Bild auf initial Zustand")}
          </button>
        </div>
      </section>
    `

    this.$ = {
      refreshButton: this.querySelector('[data-action="refresh-image"]'),
      revertButton: this.querySelector('[data-action="revert-image"]'),
      deleteButton: this.querySelector('[data-action="delete-image"]'),
    }

    this.$.refreshButton.addEventListener("click", this.handleRefreshClick.bind(this))
    this.$.revertButton.addEventListener("click", this.handleRevertClick.bind(this))
    this.$.deleteButton.addEventListener("click", this.handleDeleteClick.bind(this))
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.disabled = Boolean(state.isSending) || Boolean(state.isSessionLoading) || Boolean(state.isImageRefreshLoading)
  }

  registerSubscriptions() {
    const subscriptions = [
      ["isSending", this.onDisabledTriggerChanged.bind(this)],
      ["isSessionLoading", this.onDisabledTriggerChanged.bind(this)],
      ["isImageRefreshLoading", this.onDisabledTriggerChanged.bind(this)],
    ]

    for (const [key, listener] of subscriptions) {
      appStore.subscribe(key, listener)
    }
  }

  onDisabledTriggerChanged() {
    const state = appStore.getState()
    this._state.disabled = Boolean(state.isSending) || Boolean(state.isSessionLoading) || Boolean(state.isImageRefreshLoading)
    this.render()
  }

  handleRefreshClick() {
    appActions.refreshImage()
    if (appStore.getState().isSelectorPanelOpen) {
      appActions.toggleSelectorPanel()
    }
  }

  async handleRevertClick() {
    const hasExecuted = await appActions.revertImage()
    if (hasExecuted && appStore.getState().isSelectorPanelOpen) {
      appActions.toggleSelectorPanel()
    }
  }

  async handleDeleteClick() {
    const hasExecuted = await appActions.deleteImage()
    if (hasExecuted && appStore.getState().isSelectorPanelOpen) {
      appActions.toggleSelectorPanel()
    }
  }

  render() {
    this.$.refreshButton.disabled = this._state.disabled
    this.$.revertButton.disabled = this._state.disabled
    this.$.deleteButton.disabled = this._state.disabled
  }
}

customElements.get("sg-input-image") || customElements.define("sg-input-image", SocialGameInputImage)





