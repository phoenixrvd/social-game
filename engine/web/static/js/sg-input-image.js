import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"
import "./sg-settings-action.js"

const REFRESH_ICON = /*html*/ `
  <svg slot="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <path d="M3 3h18v18H3z"></path>
    <path d="M3 15l5-5 4 4 3-3 6 6"></path>
    <path d="M16 8h4v4"></path>
    <path d="M20 8l-4 4"></path>
  </svg>
`

const REVERT_ICON = /*html*/ `
  <svg slot="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <path d="M21 12a9 9 0 1 1-3.1-6.8"></path>
    <path d="M21 3v6h-6"></path>
  </svg>
`

const DELETE_ICON = /*html*/ `
  <svg slot="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <polyline points="3 6 5 6 21 6"></polyline>
    <path d="M19 6l-1 14H6L5 6"></path>
    <path d="M10 11v6"></path>
    <path d="M14 11v6"></path>
    <path d="M9 6V4h6v2"></path>
  </svg>
`

const CHECKBOX_CHECKED_ICON = /*html*/ `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <rect x="3" y="3" width="18" height="18" rx="3"></rect>
    <path d="M7 12l4 4 6-6"></path>
  </svg>
`

const CHECKBOX_UNCHECKED_ICON = /*html*/ `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <rect x="3" y="3" width="18" height="18" rx="3"></rect>
  </svg>
`

class SocialGameInputImage extends HTMLElement {
  constructor() {
    super()
    this._state = {
      disabled: false,
      imageAutogenerate: true,
    }

    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = /*html*/ `
      <section class="sg-settings-section">
        <h3 class="sg-settings-heading">Bild</h3>
        <div class="sg-settings-actions">
          <sg-settings-action data-action="toggle-autogenerate" aria-pressed="true" aria-label="Automatische Bildgenerierung">
              <span slot="icon" data-element="autogenerate-action-icon">${CHECKBOX_CHECKED_ICON}</span>
              <span>Automatische Bildgenerierung</span>
              <span slot="description">Bilder werden automatisch neu generiert und mit dem Chatverlauf konsistent gehalten</span>
          </sg-settings-action>
          <sg-settings-action data-action="refresh-image" aria-label="Neues Bild generieren">
              ${REFRESH_ICON}
              <span>Neues Bild generieren</span>
              <span slot="description">Erzeugt ein neues Bild aus dem aktuellen Chat-Kontext</span>
          </sg-settings-action>
          <sg-settings-action data-action="revert-image" aria-label="Vorheriges Bild laden">
              ${REVERT_ICON}
              <span>Vorheriges Bild laden</span>
              <span slot="description">Stellt vorheriges Bild wieder her und löscht aktuelles</span>
          </sg-settings-action>
          <sg-settings-action data-action="delete-image" danger aria-label="Bild zurücksetzen">
              ${DELETE_ICON}
              <span>Bild zurücksetzen</span>
              <span slot="description">Setzt das Bild auf initial Zustand</span>
          </sg-settings-action>
        </div>
      </section>
    `

    this.$ = {
      autogenerateButton: this.querySelector('[data-action="toggle-autogenerate"]'),
      autogenerateActionIcon: this.querySelector('[data-element="autogenerate-action-icon"]'),
      refreshButton: this.querySelector('[data-action="refresh-image"]'),
      revertButton: this.querySelector('[data-action="revert-image"]'),
      deleteButton: this.querySelector('[data-action="delete-image"]'),
    }

    this.$.autogenerateButton.addEventListener("click", this.handleAutogenerateClick.bind(this))
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
    this._state.imageAutogenerate = state.imageAutogenerate !== false
  }

  registerSubscriptions() {
    const subscriptions = [
      ["isSending", this.onDisabledTriggerChanged.bind(this)],
      ["isSessionLoading", this.onDisabledTriggerChanged.bind(this)],
      ["isImageRefreshLoading", this.onDisabledTriggerChanged.bind(this)],
      ["imageAutogenerate", this.onAutogenerateChanged.bind(this)],
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

  onAutogenerateChanged() {
    this._state.imageAutogenerate = appStore.getState().imageAutogenerate !== false
    this.render()
  }

  handleAutogenerateClick() {
    appActions.toggleImageAutogenerate()
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

  _renderAutogenerateButton() {
    const checked = this._state.imageAutogenerate
    const icon = checked ? CHECKBOX_CHECKED_ICON : CHECKBOX_UNCHECKED_ICON
    this.$.autogenerateActionIcon.innerHTML = icon
    this.$.autogenerateButton.setAttribute("aria-pressed", String(checked))
    this.$.autogenerateButton.toggleAttribute("inactive", !checked)
  }

  render() {
    this._renderAutogenerateButton()
    this.$.autogenerateButton.disabled = this._state.disabled
    this.$.refreshButton.disabled = this._state.disabled
    this.$.revertButton.disabled = this._state.disabled
    this.$.deleteButton.disabled = this._state.disabled
  }
}

customElements.get("sg-input-image") || customElements.define("sg-input-image", SocialGameInputImage)
