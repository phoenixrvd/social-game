import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"
import { CHECKBOX_CHECKED_ICON, CHECKBOX_UNCHECKED_ICON, DELETE_ICON, REFRESH_IMAGE_ICON, REVERT_ICON } from "./icons.js"
import "./sg-settings-action.js"

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
              <span slot="icon">${REFRESH_IMAGE_ICON}</span>
              <span>Neues Bild generieren</span>
              <span slot="description">Erzeugt ein neues Bild aus dem aktuellen Chat-Kontext</span>
          </sg-settings-action>
          <sg-settings-action data-action="revert-image" aria-label="Vorheriges Bild wiederherstellen">
              <span slot="icon">${REVERT_ICON}</span>
              <span>Vorheriges Bild wiederherstellen</span>
              <span slot="description">Ersetzt das aktuelle Bild durch den vorherigen Bildstand</span>
          </sg-settings-action>
          <sg-settings-action data-action="delete-image" danger aria-label="Aktuelles Bild löschen">
              <span slot="icon">${DELETE_ICON}</span>
              <span>Aktuelles Bild löschen</span>
              <span slot="description">Entfernt das aktuelle Bild, ohne ein früheres Bild wiederherzustellen</span>
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
