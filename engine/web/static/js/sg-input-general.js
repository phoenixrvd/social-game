import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"

const THEME_DARK_ICON = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <circle cx="12" cy="12" r="4"></circle>
    <path d="M12 2v2"></path>
    <path d="M12 20v2"></path>
    <path d="M4.93 4.93l1.41 1.41"></path>
    <path d="M17.66 17.66l1.41 1.41"></path>
    <path d="M2 12h2"></path>
    <path d="M20 12h2"></path>
    <path d="M6.34 17.66l-1.41 1.41"></path>
    <path d="M19.07 4.93l-1.41 1.41"></path>
  </svg>
`

const THEME_LIGHT_ICON = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"></path>
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

function getThemeToggleIcon(theme) {
  return theme === "dark" ? THEME_DARK_ICON : THEME_LIGHT_ICON
}

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

class SocialGameInputGeneral extends HTMLElement {
  constructor() {
    super()
    this._state = {
      disabled: false,
      theme: "dark",
    }

    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = `
      <section class="sg-settings-section">
        <h3 class="sg-settings-heading">Allgemein</h3>
        <div class="sg-settings-actions">
          <button type="button" data-action="toggle-theme" class="sg-settings-action" aria-label="Theme wechseln"></button>
          <button type="button" data-action="reset-active-npc" class="sg-settings-action sg-settings-action-danger" aria-label="Verlauf löschen">
            ${renderActionContent(DELETE_ICON, "Verlauf löschen", "Entfernt Nachrichten und Bilder der aktiven Konversation")}
          </button>
        </div>
      </section>
    `

    this.$ = {
      themeButton: this.querySelector('[data-action="toggle-theme"]'),
      resetButton: this.querySelector('[data-action="reset-active-npc"]'),
    }

    this.$.themeButton.addEventListener("click", this.handleThemeClick.bind(this))
    this.$.resetButton.addEventListener("click", this.handleResetClick.bind(this))
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.theme = state.theme === "light" ? "light" : "dark"
    this._state.disabled = Boolean(state.isSending) || Boolean(state.isSessionLoading)
  }

  registerSubscriptions() {
    const subscriptions = [
      ["theme", this.onThemeChanged.bind(this)],
      ["isSending", this.onDisabledTriggerChanged.bind(this)],
      ["isSessionLoading", this.onDisabledTriggerChanged.bind(this)],
    ]

    for (const [key, listener] of subscriptions) {
      appStore.subscribe(key, listener)
    }
  }

  onThemeChanged(theme) {
    this._state.theme = theme === "light" ? "light" : "dark"
    this.render()
  }

  onDisabledTriggerChanged() {
    const state = appStore.getState()
    this._state.disabled = Boolean(state.isSending) || Boolean(state.isSessionLoading)
    this.render()
  }

  handleThemeClick() {
    appActions.toggleTheme()
    if (appStore.getState().isSelectorPanelOpen) {
      appActions.toggleSelectorPanel()
    }
  }

  async handleResetClick() {
    const hasExecuted = await appActions.resetNpc()
    if (hasExecuted && appStore.getState().isSelectorPanelOpen) {
      appActions.toggleSelectorPanel()
    }
  }

  render() {
    this.$.themeButton.innerHTML = renderActionContent(
      getThemeToggleIcon(this._state.theme),
      "Theme wechseln",
      "Zwischen hellem und dunklem Design wechseln"
    )
    this.$.themeButton.disabled = this._state.disabled
    this.$.resetButton.disabled = this._state.disabled
  }
}

customElements.get("sg-input-general") || customElements.define("sg-input-general", SocialGameInputGeneral)





