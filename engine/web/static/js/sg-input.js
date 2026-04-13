import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"

const SVG_SEND = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-md" aria-hidden="true">
    <path d="M22 2L11 13" pathLength="1"></path>
    <path d="M22 2L15 22L11 13L2 9L22 2Z" pathLength="1"></path>
  </svg>
`

const SVG_REFRESH = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <path d="M3 3h18v18H3z"></path>
    <path d="M3 15l5-5 4 4 3-3 6 6"></path>
    <path d="M16 8h4v4"></path>
    <path d="M20 8l-4 4"></path>
  </svg>
`

const SVG_THEME_DARK = `
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

const SVG_THEME_LIGHT = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"></path>
  </svg>
`

const SVG_SELECTOR = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <line x1="21" y1="4" x2="14" y2="4"></line>
    <line x1="10" y1="4" x2="3" y2="4"></line>
    <line x1="21" y1="12" x2="12" y2="12"></line>
    <line x1="8" y1="12" x2="3" y2="12"></line>
    <line x1="21" y1="20" x2="16" y2="20"></line>
    <line x1="12" y1="20" x2="3" y2="20"></line>
    <line x1="14" y1="2" x2="14" y2="6"></line>
    <line x1="8" y1="10" x2="8" y2="14"></line>
    <line x1="16" y1="18" x2="16" y2="22"></line>
  </svg>
`

const SVG_DELETE = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
    <polyline points="3 6 5 6 21 6"></polyline>
    <path d="M19 6l-1 14H6L5 6"></path>
    <path d="M10 11v6"></path>
    <path d="M14 11v6"></path>
    <path d="M9 6V4h6v2"></path>
  </svg>
`

function getThemeToggleIcon(theme) {
  return theme === "dark" ? SVG_THEME_DARK : SVG_THEME_LIGHT
}

function renderOptions(options, selectedValue) {
  return options
    .map((option) => {
      const selected = option.id === selectedValue ? ' selected="selected"' : ""
      return `<option value="${option.id}"${selected}>${option.label}</option>`
    })
    .join("")
}

class SocialGameInput extends HTMLElement {
  constructor() {
    super()
    this._state = {
      input: "",
      isSending: false,
      isSessionLoading: false,
      isImageRefreshLoading: false,
      errorMessage: "",
      isSelectorPanelOpen: false,
      theme: localStorage.getItem("theme") === "light" ? "light" : "dark",
      npcs: [],
      scenes: [],
      npcId: "",
      sceneId: "",
    }

    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = `
      <form class="sg-chat-form" aria-busy="false">
        <div class="sg-session-row sg-hidden">
          <label class="sg-selector-field">
            <span class="sg-selector-legend">NPC</span>
            <select class="sg-npc-select sg-session-select"></select>
          </label>
          <label class="sg-selector-field">
            <span class="sg-selector-legend">Szene</span>
            <select class="sg-scene-select sg-session-select"></select>
          </label>
        </div>

        <div class="sg-composer-row">
          <label for="sg-chat-input" class="sg-visually-hidden">Nachricht eingeben</label>
          <div class="sg-input-shell">
            <textarea
              id="sg-chat-input"
              class="sg-chat-input sg-chat-textarea"
              rows="1"
              placeholder="Nachricht eingeben..."
            ></textarea>

            <button type="submit" class="sg-send-button" aria-label="Senden">
              ${SVG_SEND}
            </button>
          </div>
        </div>

        <div class="sg-composer-footer">
          <div class="sg-composer-meta" role="status" aria-live="polite">
            <span class="sg-keyboard-hint">Enter = senden, Shift+Enter = neue Zeile</span>
          </div>

          <div class="sg-composer-tools" aria-label="Werkzeuge">
            <button
              type="button"
              data-action="refresh-image"
              class="sg-toolbar-button"
              aria-label="Bild aktualisieren"
            >
              ${SVG_REFRESH}
            </button>
            <button
              type="button"
              data-action="toggle-selector"
              class="sg-toolbar-button"
              aria-label="NPC und Szene anzeigen"
              aria-pressed="false"
            >
              ${SVG_SELECTOR}
            </button>
            <button
              type="button"
              data-action="toggle-theme"
              class="sg-toolbar-button"
              aria-label="Theme wechseln"
            >
              ${getThemeToggleIcon(this._state.theme)}
            </button>
            <button
              type="button"
              data-action="reset-active-npc"
              class="sg-toolbar-button sg-toolbar-button-danger"
              aria-label="Verlauf löschen"
            >
              ${SVG_DELETE}
            </button>
          </div>
        </div>
      </form>
    `

    this.$ = {
      form: this.querySelector(".sg-chat-form"),
      sessionRow: this.querySelector(".sg-session-row"),
      npcSelect: this.querySelector(".sg-npc-select"),
      sceneSelect: this.querySelector(".sg-scene-select"),
      textarea: this.querySelector(".sg-chat-input"),
      sendButton: this.querySelector(".sg-send-button"),
      meta: this.querySelector(".sg-composer-meta"),
      refreshButton: this.querySelector('[data-action="refresh-image"]'),
      selectorButton: this.querySelector('[data-action="toggle-selector"]'),
      themeButton: this.querySelector('[data-action="toggle-theme"]'),
      resetButton: this.querySelector('[data-action="reset-active-npc"]'),
    }

    this.$.form.addEventListener("submit", this.handleSubmit.bind(this))
    this.$.sendButton.addEventListener("pointerdown", this.handleSendPointerDown.bind(this))
    this.$.textarea.addEventListener("input", this.handleInput.bind(this))
    this.$.textarea.addEventListener("keydown", this.handleKeyDown.bind(this))
    this.$.npcSelect.addEventListener("change", this.handleNpcChange.bind(this))
    this.$.sceneSelect.addEventListener("change", this.handleSceneChange.bind(this))

    this.$.refreshButton.addEventListener("click", this.handleRefreshImage.bind(this))
    this.$.selectorButton.addEventListener("click", this.handleSelectorToggle.bind(this))
    this.$.themeButton.addEventListener("click", this.handleThemeToggle.bind(this))
    this.$.resetButton.addEventListener("click", this.handleResetNpc.bind(this))

    const subscriptions = [
      ["input", this.onInputChanged.bind(this)],
      ["isSending", this.onIsSendingChanged.bind(this)],
      ["isSessionLoading", this.onSessionLoadingChanged.bind(this)],
      ["isImageRefreshLoading", this.onImageRefreshChanged.bind(this)],
      ["errorMessage", this.onErrorMessageChanged.bind(this)],
      ["isSelectorPanelOpen", this.onSelectorPanelChanged.bind(this)],
      ["theme", this.onThemeChanged.bind(this)],
      ["npcs", this.onNpcsChanged.bind(this)],
      ["scenes", this.onScenesChanged.bind(this)],
      ["npcId", this.onNpcIdChanged.bind(this)],
      ["sceneId", this.onSceneIdChanged.bind(this)],
    ]

    for (const [key, listener] of subscriptions) {
      appStore.subscribe(key, listener)
    }

    this.render()
  }

  onInputChanged(input) {
    this._state.input = typeof input === "string" ? input : ""
    this.render()
  }

  onIsSendingChanged(isSending) {
    this._state.isSending = Boolean(isSending)
    this.render()
  }

  onSessionLoadingChanged(isSessionLoading) {
    this._state.isSessionLoading = Boolean(isSessionLoading)
    this.render()
  }

  onImageRefreshChanged(isImageRefreshLoading) {
    this._state.isImageRefreshLoading = Boolean(isImageRefreshLoading)
    this.render()
  }

  onErrorMessageChanged(errorMessage) {
    this._state.errorMessage = typeof errorMessage === "string" ? errorMessage : ""
    this.render()
  }

  onSelectorPanelChanged(isSelectorPanelOpen) {
    this._state.isSelectorPanelOpen = Boolean(isSelectorPanelOpen)
    this.render()
  }

  onThemeChanged(theme) {
    this._state.theme = theme === "light" ? "light" : "dark"
    this.render()
  }

  onNpcsChanged(npcs) {
    this._state.npcs = Array.isArray(npcs) ? npcs : []
    this.render()
  }

  onScenesChanged(scenes) {
    this._state.scenes = Array.isArray(scenes) ? scenes : []
    this.render()
  }

  onNpcIdChanged(npcId) {
    this._state.npcId = typeof npcId === "string" ? npcId : ""
    this.render()
  }

  onSceneIdChanged(sceneId) {
    this._state.sceneId = typeof sceneId === "string" ? sceneId : ""
    this.render()
  }

  focusInput() {
    const textarea = this.$.textarea
    if (!(textarea instanceof HTMLTextAreaElement) || textarea.disabled) {
      return
    }
    textarea.focus()
    const length = textarea.value.length
    textarea.setSelectionRange(length, length)
  }

  syncTextareaHeight() {
    const textarea = this.$.textarea
    if (!(textarea instanceof HTMLTextAreaElement)) {
      return
    }
    textarea.style.height = "auto"
    textarea.style.height = `${Math.max(textarea.scrollHeight, 46)}px`
  }

  isSubmitBlocked() {
    return this._state.isSending || this._state.isSessionLoading
  }

  handleSubmit(event) {
    event.preventDefault()
    if (this.isSubmitBlocked()) {
      return
    }
    appActions.submitMessage(this.$.textarea.value)
  }

  handleInput(event) {
    this.syncTextareaHeight()
    appActions.setInput(event.currentTarget.value)
  }

  handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      if (this.isSubmitBlocked()) {
        return
      }
      appActions.submitMessage(this.$.textarea.value)
    }
  }

  handleNpcChange(event) {
    appActions.updateSession({
      npc_id: event.currentTarget.value,
      scene_id: this._state.sceneId,
    })
  }

  handleSceneChange(event) {
    appActions.updateSession({
      npc_id: this._state.npcId,
      scene_id: event.currentTarget.value,
    })
  }

  handleRefreshImage() {
    appActions.refreshImage()
  }

  handleSelectorToggle() {
    appActions.toggleSelectorPanel()
  }

  handleThemeToggle() {
    appActions.toggleTheme()
  }

  handleResetNpc() {
    appActions.resetNpc()
  }

  handleSendPointerDown(event) {
    // Keep textarea focused so mobile keyboards do not collapse when tapping send.
    event.preventDefault()
    this.focusInput()
  }

  render() {
    const controlsDisabled = this._state.isSending || this._state.isSessionLoading
    const composerReadOnly = this._state.isSessionLoading
    const errorText = this._state.errorMessage

    this.$.form.setAttribute("aria-busy", controlsDisabled ? "true" : "false")
    this.$.sessionRow.classList.toggle("sg-hidden", !this._state.isSelectorPanelOpen)

    this.$.npcSelect.innerHTML = renderOptions(this._state.npcs, this._state.npcId)
    this.$.sceneSelect.innerHTML = renderOptions(this._state.scenes, this._state.sceneId)
    this.$.npcSelect.disabled = controlsDisabled
    this.$.sceneSelect.disabled = controlsDisabled

    this.$.textarea.readOnly = composerReadOnly
    this.$.textarea.setAttribute("aria-readonly", composerReadOnly ? "true" : "false")
    this.$.textarea.value = this._state.input

    this.$.sendButton.className = this._state.isSending ? "sg-send-button is-loading" : "sg-send-button"
    this.$.sendButton.disabled = controlsDisabled

    this.$.meta.className = errorText ? "sg-composer-meta sg-composer-meta-error" : "sg-composer-meta"
    if (errorText) {
      this.$.meta.textContent = errorText
    } else {
      this.$.meta.innerHTML = '<span class="sg-keyboard-hint">Enter = senden, Shift+Enter = neue Zeile</span>'
    }

    this.$.refreshButton.disabled = controlsDisabled || this._state.isImageRefreshLoading
    this.$.selectorButton.setAttribute("aria-pressed", this._state.isSelectorPanelOpen ? "true" : "false")
    this.$.themeButton.innerHTML = getThemeToggleIcon(this._state.theme)
    this.$.resetButton.disabled = controlsDisabled

    this.syncTextareaHeight()
  }
}

customElements.get("sg-input") || customElements.define("sg-input", SocialGameInput)
