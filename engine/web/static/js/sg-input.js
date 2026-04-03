import { trustedHtml } from "./trusted-types.js"

const ACTION_EVENT_MAP = {
  "toggle-selector": "sg:selector-toggle",
  "toggle-theme": "sg:theme-toggle",
  "refresh-image": "sg:image-refresh",
  "reset-active-npc": "sg:reset-active-npc",
}

const INITIAL_FIELD_LTM = "ltm"
const INITIAL_LABEL_LTM = "Long-Term-Memory"

const SVG_EDIT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"></path></svg>'
const SVG_SAVE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>'
const SVG_REVERT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 .49-5L1 10"></path></svg>'
const SVG_CLOSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'

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

const SVG_SEND = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-md">
    <path d="M22 2L11 13" pathLength="1"></path>
    <path d="M22 2L15 22L11 13L2 9L22 2Z" pathLength="1"></path>
  </svg>
`

const SVG_SELECTOR = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm">
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

const SVG_IMAGE_REFRESH = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm">
    <path d="M3 3h18v18H3z"></path>
    <path d="M3 15l5-5 4 4 3-3 6 6"></path>
    <path d="M16 8h4v4"></path>
    <path d="M20 8l-4 4"></path>
  </svg>
`

const SVG_DELETE = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm">
    <polyline points="3 6 5 6 21 6"></polyline>
    <path d="M19 6l-1 14H6L5 6"></path>
    <path d="M10 11v6"></path>
    <path d="M14 11v6"></path>
    <path d="M9 6V4h6v2"></path>
  </svg>
`

const CLASS_ICON_BUTTON = "icon-button sg-toolbar-button"

function getSelectorPanelClassName(isOpen) {
  return isOpen ? "sg-selector-grid" : "sg-hidden"
}

function getSelectorButtonClassName(isOpen) {
  return isOpen ? "icon-button icon-button-active sg-toolbar-button" : CLASS_ICON_BUTTON
}

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
}

function getThemeToggleIcon(theme) {
  if (theme === "dark") {
    return SVG_THEME_DARK
  }

  return SVG_THEME_LIGHT
}

function renderOptions(options, value) {
  return options
    .map((option) => {
      const selected = option.id === value ? ' selected="selected"' : ""
      return `<option value="${escapeHtml(option.id)}"${selected}>${escapeHtml(option.label)}</option>`
    })
    .join("")
}

function getThemeToggleMeta(theme) {
  const isDark = theme === "dark"
  return {
    label: isDark ? "Helles Theme aktivieren" : "Dunkles Theme aktivieren",
    pressed: isDark ? "true" : "false",
  }
}

function renderInitialEditorSection(state, controlsDisabled) {
  const unavailable = Boolean(state.initialUnavailable)
  const canEdit = Boolean(state.canEditInitial) && !unavailable
  const disabledAttr = controlsDisabled ? "disabled" : ""
  const unavailableBlock = unavailable
    ? '<div class="sg-initial-state-unavailable" role="status">Initialzustand nicht verfuegbar</div>'
    : ""
  const errorBlock = state.initialErrorMessage
    ? `<div class="sg-initial-state-error" role="status" aria-live="assertive">${escapeHtml(state.initialErrorMessage)}</div>`
    : ""

  const field = INITIAL_FIELD_LTM
  const isEditing = Boolean(state.initialEdit?.[field])
  const value = typeof state.initial?.[field] === "string" ? state.initial[field] : ""
  const savedValue = typeof state.initialSaved?.[field] === "string" ? state.initialSaved[field] : ""
  const isDirty = value !== savedValue
  const actions = !canEdit
    ? ""
    : isEditing
      ? `
        ${isDirty ? `<button type="button" class="sg-initial-icon-button" data-action="initial-save" data-field="${field}" aria-label="Speichern" title="Speichern" ${disabledAttr}>${SVG_SAVE}</button>` : ""}
        ${isDirty ? `<button type="button" class="sg-initial-icon-button" data-action="initial-revert" data-field="${field}" aria-label="Revert" title="Revert" ${disabledAttr}>${SVG_REVERT}</button>` : ""}
        <button type="button" class="sg-initial-icon-button" data-action="initial-toggle-edit" data-field="${field}" aria-label="Schliessen" title="Schliessen" ${disabledAttr}>${SVG_CLOSE}</button>
      `
      : `<button type="button" class="sg-initial-icon-button" data-action="initial-toggle-edit" data-field="${field}" aria-label="Bearbeiten" title="Bearbeiten" ${disabledAttr}>${SVG_EDIT}</button>`

  const fieldMarkup = `
    <section class="sg-initial-card">
      <div class="sg-initial-header">
        <strong class="sg-initial-title">${INITIAL_LABEL_LTM}</strong>
        <div class="sg-initial-actions">${actions}</div>
      </div>
      ${isEditing
        ? `<textarea class="sg-initial-textarea" data-field="${field}" rows="1" ${disabledAttr}>${escapeHtml(value)}</textarea>`
        : `<pre class="sg-initial-preview">${escapeHtml(value)}</pre>`}
    </section>
  `

  return `
    <div class="sg-initial-state-section">
      ${unavailableBlock}
      ${errorBlock}
      ${fieldMarkup}
    </div>
  `
}

class SocialGameInput extends HTMLElement {
  constructor() {
    super()
    this._state = {
      input: "",
      isSending: false,
      isSessionLoading: false,
      isImageLoading: false,
      isImageRefreshLoading: false,
      errorMessage: "",
      imageUpdateError: "",
      selectorPanelOpen: false,
      theme: "dark",
      npcs: [],
      scenes: [],
      npcId: "",
      sceneId: "",
      initial: { scene: "", character: "", ltm: "" },
      initialSaved: { scene: "", character: "", ltm: "" },
      initialEdit: { scene: false, character: false, ltm: false },
      initialUnavailable: false,
      initialErrorMessage: "",
      canEditInitial: true,
    }
    this._boundHandleSubmit = this.handleSubmit.bind(this)
    this._boundHandleInput = this.handleInput.bind(this)
    this._boundHandleKeyDown = this.handleKeyDown.bind(this)
    this._boundHandleClick = this.handleClick.bind(this)
    this._boundHandleChange = this.handleChange.bind(this)
  }

  connectedCallback() {
    this.addEventListener("submit", this._boundHandleSubmit)
    this.addEventListener("input", this._boundHandleInput)
    this.addEventListener("keydown", this._boundHandleKeyDown)
    this.addEventListener("click", this._boundHandleClick)
    this.addEventListener("change", this._boundHandleChange)
    this.render()
  }

  disconnectedCallback() {
    this.removeEventListener("submit", this._boundHandleSubmit)
    this.removeEventListener("input", this._boundHandleInput)
    this.removeEventListener("keydown", this._boundHandleKeyDown)
    this.removeEventListener("click", this._boundHandleClick)
    this.removeEventListener("change", this._boundHandleChange)
  }

  setState(nextState = {}) {
    this._state = { ...this._state, ...nextState }
    this.render()
  }

  focusInput() {
    const input = this.querySelector(".sg-chat-input")
    if (!input || input.disabled) {
      return
    }
    input.focus()
    const length = input.value.length
    input.setSelectionRange(length, length)
  }

  measureFormHeight() {
    return this.querySelector(".sg-chat-form")?.getBoundingClientRect().height || 0
  }

  syncTextareaHeight() {
    const input = this.querySelector(".sg-chat-input")
    if (!input) {
      return
    }
    input.style.height = "0px"
    input.style.height = `${Math.min(input.scrollHeight, 220)}px`
  }

  syncInitialTextareaHeight() {
    const textarea = this.querySelector('.sg-initial-textarea[data-field="ltm"]')
    if (!(textarea instanceof HTMLTextAreaElement)) {
      return
    }
    textarea.style.height = "auto"
    textarea.style.height = `${textarea.scrollHeight}px`
  }

  emit(name, detail = {}) {
    this.dispatchEvent(new CustomEvent(name, { bubbles: true, composed: true, detail }))
  }

  handleSubmit(event) {
    if (!(event.target instanceof HTMLFormElement)) {
      return
    }

    event.preventDefault()
    this.emit("sg:message-submit", { message: this.querySelector(".sg-chat-input")?.value ?? "" })
  }

  handleInput(event) {
    if (!(event.target instanceof HTMLTextAreaElement)) {
      return
    }

    if (event.target.classList.contains("sg-initial-textarea")) {
      const field = event.target.getAttribute("data-field")
      if (field !== INITIAL_FIELD_LTM) {
        return
      }
      this._state.initial = { ...this._state.initial, ltm: event.target.value }
      event.target.style.height = "auto"
      event.target.style.height = `${event.target.scrollHeight}px`
      this.emit("sg:initial-draft-change", { field, value: event.target.value })
      return
    }

    if (!event.target.classList.contains("sg-chat-input")) {
      return
    }

    this._state.input = event.target.value
    this.syncTextareaHeight()
    this.emit("sg:input-change", { value: event.target.value })
  }

  handleKeyDown(event) {
    if (!(event.target instanceof HTMLTextAreaElement) || !event.target.classList.contains("sg-chat-input")) {
      return
    }

    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      this.emit("sg:message-submit", { message: event.target.value })
    }
  }

  handleClick(event) {
    const target = event.target instanceof Element ? event.target.closest("[data-action]") : null
    if (!target) {
      return
    }
    const action = target.getAttribute("data-action")

    if (action && action.startsWith("initial-")) {
      const field = target.getAttribute("data-field")
      if (field !== INITIAL_FIELD_LTM) {
        return
      }
      this.emit("sg:initial-action", { action, field })
      return
    }

    const eventName = action ? ACTION_EVENT_MAP[action] : ""
    if (eventName) {
      this.emit(eventName)
    }
  }

  handleChange(event) {
    if (!(event.target instanceof HTMLSelectElement)) {
      return
    }

    let payload = null
    if (event.target.classList.contains("sg-npc-select")) {
      payload = { npc_id: event.target.value, scene_id: this._state.sceneId }
    } else if (event.target.classList.contains("sg-scene-select")) {
      payload = { npc_id: this._state.npcId, scene_id: event.target.value }
    }

    if (payload) {
      this.emit("sg:session-change", payload)
    }
  }

  renderComposerHint() {
    const error = this._state.errorMessage || this._state.imageUpdateError
    if (error) {
      return {
        text: error,
        className: "sg-composer-hint sg-composer-hint-error",
        ariaLive: "assertive",
      }
    }

    return {
      text: "Enter = senden, Shift+Enter = neue Zeile",
      className: "sg-composer-hint sg-composer-hint-default",
      ariaLive: "polite",
    }
  }

  render() {
    const inputElement = this.querySelector(".sg-chat-input")
    const inputWasFocused = inputElement && document.activeElement === inputElement
    const initialTextareaElement = this.querySelector('.sg-initial-textarea[data-field="ltm"]')
    const initialTextareaWasFocused = initialTextareaElement && document.activeElement === initialTextareaElement
    const initialSelectionStart = initialTextareaWasFocused && initialTextareaElement instanceof HTMLTextAreaElement
      ? initialTextareaElement.selectionStart
      : null
    const initialSelectionEnd = initialTextareaWasFocused && initialTextareaElement instanceof HTMLTextAreaElement
      ? initialTextareaElement.selectionEnd
      : null
    const hint = this.renderComposerHint()
    const controlsDisabled = this._state.isSending || this._state.isSessionLoading
    const isLoading = controlsDisabled || this._state.isImageLoading || this._state.isImageRefreshLoading
    const selectorPanelClassName = getSelectorPanelClassName(this._state.selectorPanelOpen)
    const selectorButtonClassName = getSelectorButtonClassName(this._state.selectorPanelOpen)
    const themeToggleMeta = getThemeToggleMeta(this._state.theme)

    this.innerHTML = trustedHtml(`
      <form class="sg-chat-form sg-chat-form-shell chat-form-safe" aria-busy="${controlsDisabled ? "true" : "false"}">
        <div class="sg-composer-row">
          <label for="sg-chat-input" class="sg-visually-hidden">Nachricht eingeben</label>
          <textarea
            id="sg-chat-input"
            rows="1"
            class="sg-chat-input sg-chat-textarea input-scrollbar"
            placeholder="Nachricht eingeben..."
            aria-describedby="sg-composer-hint"
            ${this._state.isSessionLoading ? "disabled" : ""}
          >${escapeHtml(this._state.input)}</textarea>

          <button
            type="submit"
            class="sg-send-button${isLoading ? " is-loading" : ""}"
            aria-label="Senden"
            ${controlsDisabled ? "disabled" : ""}
          >
            ${SVG_SEND}
          </button>
        </div>

        <div class="sg-selector-panel ${selectorPanelClassName}">
          ${renderInitialEditorSection(this._state, controlsDisabled)}
          <label class="sg-selector-field">
            <span class="sg-selector-legend">NPC</span>
            <select
              class="sg-npc-select sg-session-select"
              ${controlsDisabled ? "disabled" : ""}
            >${renderOptions(this._state.npcs, this._state.npcId)}</select>
          </label>
          <label class="sg-selector-field">
            <span class="sg-selector-legend">Szene</span>
            <select
              class="sg-scene-select sg-session-select"
              ${controlsDisabled ? "disabled" : ""}
            >${renderOptions(this._state.scenes, this._state.sceneId)}</select>
          </label>
        </div>

        <div class="sg-composer-meta">
          <span id="sg-composer-hint" class="${hint.className}" role="status" aria-live="${hint.ariaLive}">${hint.text}</span>
          <div class="sg-meta-actions">
            <button
              data-action="toggle-selector"
              type="button"
              class="${selectorButtonClassName}"
              aria-label="NPC und Szene auswählen"
              aria-pressed="${this._state.selectorPanelOpen ? "true" : "false"}"
              title="NPC und Szene auswählen"
            >
              ${SVG_SELECTOR}
            </button>
            <button
              data-action="toggle-theme"
              type="button"
              class="${CLASS_ICON_BUTTON}"
              aria-label="${themeToggleMeta.label}"
              aria-pressed="${themeToggleMeta.pressed}"
              title="${themeToggleMeta.label}"
            >${getThemeToggleIcon(this._state.theme)}</button>
            <button
              data-action="refresh-image"
              type="button"
              class="${CLASS_ICON_BUTTON}"
              aria-label="Bild aktualisieren"
              title="Bild aktualisieren"
              ${controlsDisabled ? "disabled" : ""}
            >
              ${SVG_IMAGE_REFRESH}
            </button>
            <button
              data-action="reset-active-npc"
              type="button"
              class="sg-toolbar-button sg-toolbar-button-danger"
              aria-label="NPC-Daten löschen"
              title="NPC-Daten löschen"
              ${controlsDisabled ? "disabled" : ""}
            >
              ${SVG_DELETE}
            </button>
          </div>
        </div>
      </form>
    `)

    const input = this.querySelector(".sg-chat-input")
    if (input) {
      input.value = this._state.input
    }
    this.syncTextareaHeight()
    this.syncInitialTextareaHeight()

    if (inputWasFocused) {
      requestAnimationFrame(() => this.focusInput())
    }

    if (initialTextareaWasFocused) {
      requestAnimationFrame(() => {
        const textarea = this.querySelector('.sg-initial-textarea[data-field="ltm"]')
        if (!(textarea instanceof HTMLTextAreaElement) || textarea.disabled) {
          return
        }
        textarea.focus()
        if (typeof initialSelectionStart === "number" && typeof initialSelectionEnd === "number") {
          textarea.setSelectionRange(initialSelectionStart, initialSelectionEnd)
        }
      })
    }
  }
}

customElements.get("sg-input") || customElements.define("sg-input", SocialGameInput)

