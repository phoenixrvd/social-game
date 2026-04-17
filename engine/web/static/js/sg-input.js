import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"

function renderSendIcon() {
  return `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-md" aria-hidden="true">
      <path d="M22 2L11 13" pathLength="1"></path>
      <path d="M22 2L15 22L11 13L2 9L22 2Z" pathLength="1"></path>
    </svg>
  `
}

function renderRefreshIcon() {
  return `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
      <path d="M3 3h18v18H3z"></path>
      <path d="M3 15l5-5 4 4 3-3 6 6"></path>
      <path d="M16 8h4v4"></path>
      <path d="M20 8l-4 4"></path>
    </svg>
  `
}

function renderRevertIcon() {
  return `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
      <path d="M3 7v6h6"></path>
      <path d="M21 17v-6h-6"></path>
      <path d="M3 13a8 8 0 0 0 14.9 3"></path>
      <path d="M21 11A8 8 0 0 0 6.1 8"></path>
    </svg>
  `
}

function renderThemeDarkIcon() {
  return `
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
}

function renderThemeLightIcon() {
  return `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
      <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"></path>
    </svg>
  `
}

function renderDeleteIcon() {
  return `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true">
      <polyline points="3 6 5 6 21 6"></polyline>
      <path d="M19 6l-1 14H6L5 6"></path>
      <path d="M10 11v6"></path>
      <path d="M14 11v6"></path>
      <path d="M9 6V4h6v2"></path>
    </svg>
  `
}

function renderGearIcon() {
  return `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-xs" aria-hidden="true">
      <circle cx="12" cy="12" r="3"></circle>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
    </svg>
  `
}

function getThemeToggleIcon(theme) {
  return theme === "dark" ? renderThemeDarkIcon() : renderThemeLightIcon()
}

function renderOptions(options, selectedValue) {
  return options
    .map((option) => {
      const selected = option.id === selectedValue ? ' selected="selected"' : ""
      return `<option value="${option.id}"${selected}>${option.label}</option>`
    })
    .join("")
}

function renderSettingsActionContent(icon, title, description = "") {
  const descriptionMarkup = description ? `<span class="sg-settings-action-text">${description}</span>` : ""
  return `
    <span class="sg-settings-action-icon" aria-hidden="true">${icon}</span>
    <span class="sg-settings-action-copy">
      <span class="sg-settings-action-title">${title}</span>
      ${descriptionMarkup}
    </span>
  `
}

class SocialGameInput extends HTMLElement {
  constructor() {
    super()
    this._state = {
      input: "",
      isSending: false,
      isAssistantTyping: false,
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
    this.innerHTML = this.renderFormMarkup()
    this.cacheElements()
    this.registerEventListeners()
    this.registerSubscriptions()
    this.render()
  }

  renderFormMarkup() {
    return `
      <form class="sg-chat-form" aria-busy="false">
        ${this.renderOptionsPanelMarkup()}
        ${this.renderComposerMarkup()}
        ${this.renderFooterMarkup()}
      </form>
    `
  }

  renderOptionsPanelMarkup() {
    return `
      <div id="sg-options-panel" class="sg-options-panel sg-hidden">
        ${this.renderContextSectionMarkup()}
        ${this.renderImageSectionMarkup()}
        ${this.renderGeneralSectionMarkup()}
      </div>
    `
  }

  renderContextSectionMarkup() {
    return `
      <section class="sg-settings-section">
        <div class="sg-session-row">
          <label class="sg-selector-field">
            <span class="sg-selector-legend">NPC</span>
            <select class="sg-npc-select sg-session-select"></select>
          </label>
          <label class="sg-selector-field">
            <span class="sg-selector-legend">Szene</span>
            <select class="sg-scene-select sg-session-select"></select>
          </label>
        </div>
      </section>
    `
  }

  renderImageSectionMarkup() {
    return `
      <section class="sg-settings-section">
        <h3 class="sg-settings-heading">Bild</h3>
        <div class="sg-settings-actions">
          <button type="button" data-action="refresh-image" class="sg-settings-action" aria-label="Bild neu generieren">
            ${renderSettingsActionContent(renderRefreshIcon(), "Bild neu generieren", "Erzeugt eine neue Variante aus dem aktuellen Kontext")}
          </button>
          <button type="button" data-action="revert-image" class="sg-settings-action" aria-label="Auf letzte Version zurücksetzen">
            ${renderSettingsActionContent(renderRevertIcon(), "Auf letzte Version zurücksetzen", "Stellt vorheriges Bild wieder her")}
          </button>
          <button type="button" data-action="delete-image" class="sg-settings-action sg-settings-action-danger" aria-label="Bild zurücksetzen">
            ${renderSettingsActionContent(renderDeleteIcon(), "Bild zurücksetzen", "Setzt das Bild auf initial Zustand")}
          </button>
        </div>
      </section>
    `
  }

  renderGeneralSectionMarkup() {
    return `
      <section class="sg-settings-section">
        <h3 class="sg-settings-heading">Allgemein</h3>
        <div class="sg-settings-actions">
          <button type="button" data-action="toggle-theme" class="sg-settings-action" aria-label="Theme wechseln">
            ${renderSettingsActionContent(getThemeToggleIcon(this._state.theme), "Theme wechseln", "Zwischen hellem und dunklem Design wechseln")}
          </button>
          <button type="button" data-action="reset-active-npc" class="sg-settings-action sg-settings-action-danger" aria-label="Verlauf löschen">
            ${renderSettingsActionContent(renderDeleteIcon(), "Verlauf löschen", "Entfernt Nachrichten und Bilder der aktiven Konversation")}
          </button>
        </div>
      </section>
    `
  }

  renderComposerMarkup() {
    return `
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
            ${renderSendIcon()}
          </button>
        </div>
      </div>
    `
  }

  renderFooterMarkup() {
    return `
      <div class="sg-composer-footer">
        <div class="sg-composer-meta" role="status" aria-live="polite">
          <span class="sg-composer-error sg-hidden"></span>
          <span class="sg-composer-status sg-hidden">
            <span class="sg-visually-hidden">Antwort wird geladen</span>
            <span class="typing-dots" aria-hidden="true"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></span>
          </span>
          <span class="sg-keyboard-hint">Enter = senden, Shift+Enter = neue Zeile</span>
        </div>

        <div class="sg-composer-tools" aria-label="Werkzeuge">
          <button
            type="button"
            data-action="toggle-selector"
            class="sg-options-toggle"
            aria-label="Optionen"
            aria-controls="sg-options-panel"
            aria-expanded="false"
          >
            ${renderGearIcon()} Optionen
          </button>
        </div>
      </div>
    `
  }

  cacheElements() {
    this.$ = {
      form: this.querySelector(".sg-chat-form"),
      optionsPanel: this.querySelector(".sg-options-panel"),
      npcSelect: this.querySelector(".sg-npc-select"),
      sceneSelect: this.querySelector(".sg-scene-select"),
      textarea: this.querySelector(".sg-chat-input"),
      sendButton: this.querySelector(".sg-send-button"),
      meta: this.querySelector(".sg-composer-meta"),
      metaError: this.querySelector(".sg-composer-error"),
      typingStatus: this.querySelector(".sg-composer-status"),
      keyboardHint: this.querySelector(".sg-keyboard-hint"),
      revertButton: this.querySelector('[data-action="revert-image"]'),
      deleteImageButton: this.querySelector('[data-action="delete-image"]'),
      refreshButton: this.querySelector('[data-action="refresh-image"]'),
      optionsButton: this.querySelector('[data-action="toggle-selector"]'),
      themeButton: this.querySelector('[data-action="toggle-theme"]'),
      resetButton: this.querySelector('[data-action="reset-active-npc"]'),
    }
  }

  registerEventListeners() {
    this.$.form.addEventListener("submit", this.handleSubmit.bind(this))
    this.$.sendButton.addEventListener("pointerdown", this.handleSendPointerDown.bind(this))
    this.$.textarea.addEventListener("input", this.handleInput.bind(this))
    this.$.textarea.addEventListener("keydown", this.handleKeyDown.bind(this))
    this.$.npcSelect.addEventListener("change", this.handleNpcChange.bind(this))
    this.$.sceneSelect.addEventListener("change", this.handleSceneChange.bind(this))
    this.$.revertButton.addEventListener("click", appActions.revertImage)
    this.$.deleteImageButton.addEventListener("click", appActions.deleteImage)
    this.$.refreshButton.addEventListener("click", appActions.refreshImage)
    this.$.optionsButton.addEventListener("click", appActions.toggleSelectorPanel)
    this.$.themeButton.addEventListener("click", appActions.toggleTheme)
    this.$.resetButton.addEventListener("click", appActions.resetNpc)
    this.$.optionsPanel.addEventListener("click", this.handleOptionsPanelClick.bind(this))
  }

  registerSubscriptions() {
    const subscriptions = [
      ["input", this.onInputChanged.bind(this)],
      ["isSending", this.onIsSendingChanged.bind(this)],
      ["isAssistantTyping", this.onAssistantTypingChanged.bind(this)],
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
  }

  onInputChanged(input) {
    this._state.input = typeof input === "string" ? input : ""
    this.render()
  }

  onIsSendingChanged(isSending) {
    this._state.isSending = Boolean(isSending)
    this.render()
  }

  onAssistantTypingChanged(isAssistantTyping) {
    this._state.isAssistantTyping = Boolean(isAssistantTyping)
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
    if (textarea.disabled) {
      return
    }

    textarea.focus()
    const length = textarea.value.length
    textarea.setSelectionRange(length, length)
  }

  syncTextareaHeight() {
    const textarea = this.$.textarea
    const minHeight = 46

    textarea.style.height = "auto"
    textarea.style.height = `${Math.max(textarea.scrollHeight, minHeight)}px`
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
    if (this._state.isSelectorPanelOpen) {
      appActions.toggleSelectorPanel()
    }
  }

  handleSceneChange(event) {
    appActions.updateSession({
      npc_id: this._state.npcId,
      scene_id: event.currentTarget.value,
    })
    if (this._state.isSelectorPanelOpen) {
      appActions.toggleSelectorPanel()
    }
  }

  handleOptionsPanelClick(event) {
    if (event.target.closest("[data-action]") && this._state.isSelectorPanelOpen) {
      appActions.toggleSelectorPanel()
    }
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
    const optionsPanel = this.$.optionsPanel
    const meta = this.$.meta

    this.$.form.setAttribute("aria-busy", controlsDisabled ? "true" : "false")
    this.$.form.classList.toggle("is-options-open", this._state.isSelectorPanelOpen)
    this.renderOptionsPanel(controlsDisabled, optionsPanel)
    this.renderComposer(controlsDisabled, composerReadOnly, errorText, meta)

    this.syncTextareaHeight()
  }

  renderOptionsPanel(controlsDisabled, optionsPanel) {
    const imageActionsDisabled = controlsDisabled || this._state.isImageRefreshLoading

    optionsPanel.classList.toggle("sg-hidden", !this._state.isSelectorPanelOpen)
    this.$.optionsButton.setAttribute("aria-expanded", this._state.isSelectorPanelOpen ? "true" : "false")
    this.$.npcSelect.innerHTML = renderOptions(this._state.npcs, this._state.npcId)
    this.$.sceneSelect.innerHTML = renderOptions(this._state.scenes, this._state.sceneId)
    this.$.npcSelect.disabled = controlsDisabled
    this.$.sceneSelect.disabled = controlsDisabled
    this.$.refreshButton.disabled = imageActionsDisabled
    this.$.revertButton.disabled = imageActionsDisabled
    this.$.deleteImageButton.disabled = imageActionsDisabled
    this.$.themeButton.innerHTML = renderSettingsActionContent(
      getThemeToggleIcon(this._state.theme),
      "Theme wechseln",
      "Zwischen hellem und dunklem Design wechseln"
    )
    this.$.resetButton.disabled = controlsDisabled
  }

  renderComposerMeta(errorText, meta) {
    const hasError = Boolean(errorText)
    const showTyping = this._state.isAssistantTyping && !hasError

    meta.className = hasError ? "sg-composer-meta sg-composer-meta-error" : "sg-composer-meta"
    this.$.metaError.textContent = errorText
    this.$.metaError.classList.toggle("sg-hidden", !hasError)
    this.$.typingStatus.classList.toggle("sg-hidden", !showTyping)
    this.$.keyboardHint.classList.toggle("sg-hidden", hasError || showTyping)
  }

  renderComposer(controlsDisabled, composerReadOnly, errorText, meta) {
    this.$.textarea.readOnly = composerReadOnly
    this.$.textarea.setAttribute("aria-readonly", composerReadOnly ? "true" : "false")
    this.$.textarea.value = this._state.input
    this.$.sendButton.className = this._state.isSending ? "sg-send-button is-loading" : "sg-send-button"
    this.$.sendButton.disabled = controlsDisabled
    this.renderComposerMeta(errorText, meta)
  }
}

customElements.get("sg-input") || customElements.define("sg-input", SocialGameInput)
