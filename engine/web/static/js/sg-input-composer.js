import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"
import { GEAR_ICON, SEND_ICON } from "./icons.js"
import "./sg-thumbnail.js"

class SocialGameInputComposer extends HTMLElement {
  constructor() {
    super()
    this._state = {
      input: "",
      isSending: false,
      isAssistantTyping: false,
      isSessionLoading: false,
      errorMessage: "",
      isSelectorPanelOpen: false,
    }

    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = this.buildMarkup()
    this.cacheElements()
    this.registerDomEvents()
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  buildMarkup() {
    return /*html*/ `
      <div class="sg-composer-layout">
        <sg-thumbnail class="sg-composer-thumb sg-hidden"></sg-thumbnail>

        <div class="sg-composer-main">
          <div class="sg-composer-row">
            <label for="sg-chat-input" class="sg-visually-hidden">Nachricht eingeben</label>
            <textarea
              id="sg-chat-input"
              class="sg-chat-input sg-chat-textarea"
              rows="1"
              placeholder="Nachricht eingeben..."
            ></textarea>
            <button type="button" class="sg-send-button" aria-label="Senden">
              ${SEND_ICON}
            </button>
          </div>

          <div class="sg-composer-footer">
            <div class="sg-composer-meta" role="status" aria-live="polite">
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
                ${GEAR_ICON} Optionen
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="sg-composer-error-container" role="alert" aria-live="assertive">
        <span class="sg-composer-error sg-hidden"></span>
      </div>
    `
  }

  cacheElements() {
    this.$ = {
      thumbnail: this.querySelector(".sg-composer-thumb"),
      textarea: this.querySelector(".sg-chat-input"),
      sendButton: this.querySelector(".sg-send-button"),
      errorContainer: this.querySelector(".sg-composer-error-container"),
      metaError: this.querySelector(".sg-composer-error"),
      typingStatus: this.querySelector(".sg-composer-status"),
      keyboardHint: this.querySelector(".sg-keyboard-hint"),
      optionsButton: this.querySelector('[data-action="toggle-selector"]'),
    }
  }

  registerDomEvents() {
    this.$.sendButton.addEventListener("pointerdown", this.handleSendPointerDown.bind(this))
    this.$.sendButton.addEventListener("click", this.handleSubmit.bind(this))
    this.$.textarea.addEventListener("input", this.handleInput.bind(this))
    this.$.textarea.addEventListener("keydown", this.handleKeyDown.bind(this))
    this.$.optionsButton.addEventListener("click", this.handleOptionsClick.bind(this))
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.input = typeof state.input === "string" ? state.input : ""
    this._state.isSending = Boolean(state.isSending)
    this._state.isAssistantTyping = Boolean(state.isAssistantTyping)
    this._state.isSessionLoading = Boolean(state.isSessionLoading)
    this._state.errorMessage = typeof state.errorMessage === "string" ? state.errorMessage : ""
    this._state.isSelectorPanelOpen = Boolean(state.isSelectorPanelOpen)
  }

  registerSubscriptions() {
    const subscriptions = [
      ["input", this.onInputChanged.bind(this)],
      ["isSending", this.onIsSendingChanged.bind(this)],
      ["isAssistantTyping", this.onIsAssistantTypingChanged.bind(this)],
      ["isSessionLoading", this.onIsSessionLoadingChanged.bind(this)],
      ["errorMessage", this.onErrorMessageChanged.bind(this)],
      ["isSelectorPanelOpen", this.onSelectorPanelOpenChanged.bind(this)],
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

  onIsAssistantTypingChanged(isAssistantTyping) {
    this._state.isAssistantTyping = Boolean(isAssistantTyping)
    this.render()
  }

  onIsSessionLoadingChanged(isSessionLoading) {
    this._state.isSessionLoading = Boolean(isSessionLoading)
    this.render()
  }

  onErrorMessageChanged(errorMessage) {
    this._state.errorMessage = typeof errorMessage === "string" ? errorMessage : ""
    this.render()
  }

  onSelectorPanelOpenChanged(isSelectorPanelOpen) {
    this._state.isSelectorPanelOpen = Boolean(isSelectorPanelOpen)
    this.render()
  }

  focusInput() {
    if (this.$.textarea.disabled) {
      return
    }

    this.$.textarea.focus()
    const length = this.$.textarea.value.length
    this.$.textarea.setSelectionRange(length, length)
  }

  syncTextareaHeight() {
    const minHeight = 46

    this.$.textarea.style.height = "auto"
    this.$.textarea.style.height = `${Math.max(this.$.textarea.scrollHeight, minHeight)}px`
  }

  isSubmitBlocked() {
    return this._state.isSending || this._state.isSessionLoading
  }

  handleSubmit() {
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
      this.handleSubmit()
    }
  }

  handleSendPointerDown(event) {
    // Keep textarea focused so mobile keyboards do not collapse when tapping send.
    event.preventDefault()
    this.focusInput()
  }

  handleOptionsClick() {
    appActions.toggleSelectorPanel()
  }

  renderImageThumbnail() {
    const showThumbnail = !this._state.isSelectorPanelOpen

    this.$.thumbnail.classList.toggle("sg-hidden", !showThumbnail)
  }

  renderMeta() {
    const hasError = Boolean(this._state.errorMessage)
    const showTyping = this._state.isAssistantTyping && !hasError

    this.$.errorContainer.classList.toggle("sg-hidden", !hasError)
    this.$.metaError.textContent = this._state.errorMessage
    this.$.metaError.classList.toggle("sg-hidden", !hasError)
    this.$.typingStatus.classList.toggle("sg-hidden", !showTyping)
    this.$.keyboardHint.classList.toggle("sg-hidden", hasError || showTyping)
  }

  render() {
    const controlsDisabled = this._state.isSending || this._state.isSessionLoading

    this.$.textarea.readOnly = this._state.isSessionLoading
    this.$.textarea.setAttribute("aria-readonly", this._state.isSessionLoading ? "true" : "false")
    this.$.textarea.value = this._state.input
    this.$.sendButton.className = this._state.isSending ? "sg-send-button is-loading" : "sg-send-button"
    this.$.sendButton.disabled = controlsDisabled
    this.$.optionsButton.setAttribute("aria-expanded", this._state.isSelectorPanelOpen ? "true" : "false")
    this.renderImageThumbnail()
    this.renderMeta()
    this.syncTextareaHeight()
  }
}

customElements.get("sg-input-composer") || customElements.define("sg-input-composer", SocialGameInputComposer)
