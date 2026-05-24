import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"
import { DELETE_ICON, THEME_DARK_ICON, THEME_LIGHT_ICON } from "./icons.js"
import "./sg-settings-action.js"

function getThemeToggleIcon(theme) {
  return theme === "dark" ? THEME_DARK_ICON : THEME_LIGHT_ICON
}

class SocialGameInputGeneral extends HTMLElement {
  constructor() {
    super()
    this._state = {
      disabled: false,
      theme: "dark",
      userProfile: "",
      isDynamicNpc: false,
      isDynamicScene: false,
    }

    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = /*html*/ `
      <section class="sg-settings-section">
        <h3 class="sg-settings-heading">Allgemein</h3>
        <div class="sg-settings-actions">
          <sg-settings-action data-action="toggle-theme" aria-label="Theme wechseln">
              <span slot="icon" data-element="theme-action-icon">${THEME_DARK_ICON}</span>
              <span>Theme wechseln</span>
              <span slot="description">Zwischen hellem und dunklem Design wechseln</span>
          </sg-settings-action>
          <sg-settings-action data-action="reset-active-npc" danger aria-label="Verlauf löschen">
              <span slot="icon">${DELETE_ICON}</span>
              <span>Verlauf löschen</span>
              <span slot="description">Entfernt Nachrichten und Bilder der aktiven Konversation</span>
          </sg-settings-action>
          <label class="sg-settings-checkbox">
            <input id="delete-active-npc" name="delete-active-npc" type="checkbox" data-action="delete-active-npc" />
            <span>Erstellten NPC mit löschen</span>
          </label>
          <label class="sg-settings-checkbox">
            <input id="delete-active-scene" name="delete-active-scene" type="checkbox" data-action="delete-active-scene" />
            <span>Erstellte Szene mit löschen</span>
          </label>
          <label class="sg-settings-checkbox">
            <input id="delete-active-npc-context" name="delete-active-npc-context" type="checkbox" data-action="delete-active-npc-context" />
            <span>Erstellten NPC-Kontext löschen</span>
          </label>
        </div>
      </section>
      <section class="sg-settings-section">
        <h3 class="sg-selector-legend">Dein Profil</h3>
        <textarea
          id="user-profile-textarea"
          name="user-profile"
          data-element="user-profile-textarea"
          class="sg-settings-textarea chat-scrollbar"
          placeholder="Was soll der NPC über dich wissen? (Name, Beruf, Geschlecht)"
          aria-label="User Profile editieren"></textarea>
      </section>
    `

    this.$ = {
      themeButton: this.querySelector('[data-action="toggle-theme"]'),
      themeActionIcon: this.querySelector('[data-element="theme-action-icon"]'),
      resetButton: this.querySelector('[data-action="reset-active-npc"]'),
      deleteNpcCheckbox: this.querySelector('[data-action="delete-active-npc"]'),
      deleteSceneCheckbox: this.querySelector('[data-action="delete-active-scene"]'),
      deleteNpcContextCheckbox: this.querySelector('[data-action="delete-active-npc-context"]'),
      userProfileTextarea: this.querySelector('[data-element="user-profile-textarea"]'),
    }

    this.$.themeButton.addEventListener("click", this.handleThemeClick.bind(this))
    this.$.resetButton.addEventListener("click", this.handleResetClick.bind(this))
    this.$.deleteNpcCheckbox.addEventListener("change", this.render.bind(this))
    this.$.deleteSceneCheckbox.addEventListener("change", this.render.bind(this))
    this.$.userProfileTextarea.addEventListener("blur", this.handleUserProfileBlur.bind(this))
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.theme = state.theme === "light" ? "light" : "dark"
    this._state.disabled = Boolean(state.isSending) || Boolean(state.isSessionLoading)
    this._state.userProfile = state.userProfile || ""
    this._state.isDynamicNpc = Boolean(state.isDynamicNpc)
    this._state.isDynamicScene = Boolean(state.isDynamicScene)
  }

  registerSubscriptions() {
    const subscriptions = [
      ["theme", this.onThemeChanged.bind(this)],
      ["isSending", this.onDisabledTriggerChanged.bind(this)],
      ["isSessionLoading", this.onDisabledTriggerChanged.bind(this)],
      ["userProfile", this.onUserProfileChanged.bind(this)],
      ["isDynamicNpc", this.onDynamicNpcChanged.bind(this)],
      ["isDynamicScene", this.onDynamicSceneChanged.bind(this)],
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

  onDynamicSceneChanged(value) {
    this._state.isDynamicScene = Boolean(value)
    this.render()
  }

  onDynamicNpcChanged(value) {
    this._state.isDynamicNpc = Boolean(value)
    this.render()
  }

  handleThemeClick() {
    appActions.toggleTheme()
    if (appStore.getState().isSelectorPanelOpen) {
      appActions.toggleSelectorPanel()
    }
  }

  async handleResetClick() {
    const hasExecuted = await appActions.resetNpc({
      deleteNpc: this.$.deleteNpcCheckbox.checked,
      deleteScene: this.$.deleteSceneCheckbox.checked,
      deleteNpcContext: this.$.deleteNpcContextCheckbox.checked,
    })
    if (hasExecuted && appStore.getState().isSelectorPanelOpen) {
      appActions.toggleSelectorPanel()
    }
  }

  onUserProfileChanged(userProfile) {
    this._state.userProfile = userProfile || ""
    this.render()
  }

  async handleUserProfileBlur() {
    const content = this.$.userProfileTextarea.value.trim()
    await appActions.updateUserProfile(content)
  }

  render() {
    this.$.themeActionIcon.innerHTML = getThemeToggleIcon(this._state.theme)
    this.$.themeButton.disabled = this._state.disabled
    this.$.resetButton.disabled = this._state.disabled
    this.$.deleteNpcCheckbox.disabled = this._state.disabled || !this._state.isDynamicNpc
    this.$.deleteSceneCheckbox.disabled = this._state.disabled || !this._state.isDynamicScene
    if (this.$.deleteNpcCheckbox.disabled) {
      this.$.deleteNpcCheckbox.checked = false
    }
    if (this.$.deleteSceneCheckbox.disabled) {
      this.$.deleteSceneCheckbox.checked = false
    }
    if (this.$.deleteNpcCheckbox.checked) {
      this.$.deleteNpcContextCheckbox.checked = true
    }
    if (this.$.deleteSceneCheckbox.checked) {
      this.$.deleteNpcContextCheckbox.checked = true
    }
    this.$.deleteNpcContextCheckbox.disabled = this._state.disabled || this.$.deleteNpcCheckbox.checked || this.$.deleteSceneCheckbox.checked
    this.$.userProfileTextarea.value = this._state.userProfile
    this.$.userProfileTextarea.disabled = this._state.disabled
  }
}

customElements.get("sg-input-general") || customElements.define("sg-input-general", SocialGameInputGeneral)
