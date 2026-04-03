import { trustedHtml } from "./trusted-types.js"

const SVG_EDIT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"></path></svg>'
const SVG_SAVE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>'
const SVG_REVERT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 .49-5L1 10"></path></svg>'
const SVG_CLOSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
}

function sanitizeMessageHtml(rawHtml) {
  const urlAttributes = new Set(["href", "src", "xlink:href", "formaction", "poster"])
  const doc = new DOMParser().parseFromString(trustedHtml(String(rawHtml ?? "")), "text/html")

  doc.body.querySelectorAll("*").forEach((element) => {
    ;[...element.attributes].forEach((attribute) => {
      const name = attribute.name.toLowerCase()
      const value = String(attribute.value ?? "").trim()

      if (name.startsWith("on")) {
        element.removeAttribute(attribute.name)
        return
      }

      if (urlAttributes.has(name) && /^\s*javascript:/i.test(value)) {
        element.removeAttribute(attribute.name)
      }
    })
  })

  return doc.body.innerHTML
}

class SocialGameContextMessage extends HTMLElement {
  constructor() {
    super()
    this._message = null
    this._messageSnapshot = null
    this._boundHandleClick = this.handleClick.bind(this)
    this._boundHandleInput = this.handleInput.bind(this)
  }

  connectedCallback() {
    this.addEventListener("click", this._boundHandleClick)
    this.addEventListener("input", this._boundHandleInput)
    this.render()
  }

  disconnectedCallback() {
    this.removeEventListener("click", this._boundHandleClick)
    this.removeEventListener("input", this._boundHandleInput)
  }

  emit(name, detail = {}) {
    this.dispatchEvent(new CustomEvent(name, { bubbles: true, composed: true, detail }))
  }

  handleClick(event) {
    const target = event.target instanceof Element ? event.target.closest("[data-initial-action]") : null
    if (!target || !this._message) {
      return
    }

    const action = target.getAttribute("data-initial-action")
    const field = target.getAttribute("data-field")
    if (!action || !field) {
      return
    }

    this.emit("sg:initial-action", { action, field })
  }

  handleInput(event) {
    if (!(event.target instanceof HTMLTextAreaElement) || !event.target.classList.contains("sg-initial-context-textarea")) {
      return
    }

    const field = event.target.getAttribute("data-field")
    if (!field) {
      return
    }

    this.autoResizeTextarea(event.target)
    const savedValue = typeof this._message?.initialSavedValue === "string" ? this._message.initialSavedValue : ""
    const isDirty = event.target.value !== savedValue
    if (this._message && this._message.initialEditing) {
      this._message.initialValue = event.target.value
      if (Boolean(this._message.initialDirty) !== isDirty) {
        this._message.initialDirty = isDirty
        this.syncEditingActions(field, isDirty)
      }
    }
    this.emit("sg:initial-draft-change", { field, value: event.target.value })
  }

  autoResizeTextarea(textarea) {
    const chatContainer = textarea.closest(".sg-chat-messages")
    const previousChatScrollTop = chatContainer instanceof HTMLElement ? chatContainer.scrollTop : null
    const scrollingElement = document.scrollingElement
    const previousDocumentScrollTop = scrollingElement ? scrollingElement.scrollTop : null
    const previousWindowScrollX = window.scrollX
    const previousWindowScrollY = window.scrollY

    const restoreScrollPosition = () => {
      if (chatContainer instanceof HTMLElement && previousChatScrollTop !== null) {
        chatContainer.scrollTop = previousChatScrollTop
      }
      if (scrollingElement && previousDocumentScrollTop !== null) {
        scrollingElement.scrollTop = previousDocumentScrollTop
      }
      if (window.scrollX !== previousWindowScrollX || window.scrollY !== previousWindowScrollY) {
        window.scrollTo(previousWindowScrollX, previousWindowScrollY)
      }
    }

    textarea.style.height = "auto"
    textarea.style.height = `${textarea.scrollHeight}px`

    restoreScrollPosition()
    requestAnimationFrame(() => restoreScrollPosition())
  }

  syncTextareaHeight() {
    const textarea = this.querySelector(".sg-initial-context-textarea")
    if (textarea instanceof HTMLTextAreaElement) {
      this.autoResizeTextarea(textarea)
    }
  }

  createMessageSnapshot(message) {
    if (!message || typeof message !== "object") {
      return null
    }

    return {
      id: typeof message.id === "string" ? message.id : "",
      role: typeof message.role === "string" ? message.role : "",
      content: typeof message.content === "string" ? message.content : "",
      html: typeof message.html === "string" ? message.html : "",
      initialField: typeof message.initialField === "string" ? message.initialField : "",
      initialValue: typeof message.initialValue === "string" ? message.initialValue : "",
      initialSavedValue: typeof message.initialSavedValue === "string" ? message.initialSavedValue : "",
      initialDirty: Boolean(message.initialDirty),
      initialEditing: Boolean(message.initialEditing),
      initialEditable: Boolean(message.initialEditable),
    }
  }

  isSameMessageSnapshot(left, right) {
    if (!left || !right) {
      return left === right
    }

    return left.id === right.id &&
      left.role === right.role &&
      left.content === right.content &&
      left.html === right.html &&
      left.initialField === right.initialField &&
      left.initialValue === right.initialValue &&
      left.initialSavedValue === right.initialSavedValue &&
      left.initialDirty === right.initialDirty &&
      left.initialEditing === right.initialEditing &&
      left.initialEditable === right.initialEditable
  }

  shouldKeepFocusedEditor(previousSnapshot, nextSnapshot) {
    if (!previousSnapshot || !nextSnapshot?.initialEditing) {
      return false
    }

    const textarea = this.querySelector(".sg-initial-context-textarea")
    if (!(textarea instanceof HTMLTextAreaElement) || document.activeElement !== textarea) {
      return false
    }

    return previousSnapshot.id === nextSnapshot.id &&
      previousSnapshot.role === nextSnapshot.role &&
      previousSnapshot.content === nextSnapshot.content &&
      previousSnapshot.html === nextSnapshot.html &&
      previousSnapshot.initialField === nextSnapshot.initialField &&
      previousSnapshot.initialEditing === nextSnapshot.initialEditing &&
      previousSnapshot.initialEditable === nextSnapshot.initialEditable &&
      textarea.value === nextSnapshot.initialValue
  }

  set message(value) {
    const nextMessage = value && typeof value === "object" ? value : null
    const nextSnapshot = this.createMessageSnapshot(nextMessage)

    if (this.isSameMessageSnapshot(this._messageSnapshot, nextSnapshot)) {
      return
    }

    const shouldKeepFocusedEditor = this.shouldKeepFocusedEditor(this._messageSnapshot, nextSnapshot)
    this._message = nextMessage
    this._messageSnapshot = nextSnapshot

    if (!shouldKeepFocusedEditor) {
      this.render()
    }
  }

  syncEditingActions(field, isDirty) {
    const actionsContainer = this.querySelector(".sg-initial-context-actions")
    if (!(actionsContainer instanceof HTMLElement)) {
      return
    }

    actionsContainer.innerHTML = trustedHtml(this.renderEditingActions(field, isDirty))
  }

  renderEditingActions(field, isDirty) {
    return `
      ${isDirty ? `<button type="button" class="sg-initial-icon-button" data-initial-action="initial-save" data-field="${escapeHtml(field)}" aria-label="Speichern" title="Speichern">${SVG_SAVE}</button>` : ""}
      ${isDirty ? `<button type="button" class="sg-initial-icon-button" data-initial-action="initial-revert" data-field="${escapeHtml(field)}" aria-label="Revert" title="Revert">${SVG_REVERT}</button>` : ""}
      <button type="button" class="sg-initial-icon-button" data-initial-action="initial-toggle-edit" data-field="${escapeHtml(field)}" aria-label="Schliessen" title="Schliessen">${SVG_CLOSE}</button>
    `
  }

  render() {
    const message = this._message
    if (!message) {
      this.innerHTML = trustedHtml("")
      return
    }

    const field = message.initialField || ""
    const value = typeof message.initialValue === "string" ? message.initialValue : String(message.content || "")
    const isEditing = Boolean(message.initialEditing)
    const canEdit = Boolean(message.initialEditable)
    const isDirty = Boolean(message.initialDirty)
    const actions = !canEdit
      ? ""
      : isEditing
        ? this.renderEditingActions(field, isDirty)
        : `<button type="button" class="sg-initial-icon-button" data-initial-action="initial-toggle-edit" data-field="${escapeHtml(field)}" aria-label="Bearbeiten" title="Bearbeiten">${SVG_EDIT}</button>`
    const displayHtmlSource = typeof message.html === "string" && message.html.trim() ? message.html : value
    const contentMarkup = isEditing
      ? `<textarea class="sg-initial-context-textarea" data-field="${escapeHtml(field)}" rows="1">${escapeHtml(value)}</textarea>`
      : `<div class="sg-initial-context-html">${sanitizeMessageHtml(displayHtmlSource)}</div>`

    this.innerHTML = trustedHtml(`
      <div class="context-rich msg-context msg-bubble msg-bubble-context">
        ${contentMarkup}
        <div class="sg-initial-context-actions">${actions}</div>
      </div>
    `)

    if (isEditing) {
      this.syncTextareaHeight()
    }
  }
}

customElements.get("sg-context-message") || customElements.define("sg-context-message", SocialGameContextMessage)
