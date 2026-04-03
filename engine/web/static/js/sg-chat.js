import "./sg-message.js"
import "./sg-context-message.js"
import { trustedHtml } from "./trusted-types.js"

class SocialGameChat extends HTMLElement {
  constructor() {
    super()
    this._state = {
      messages: [],
      isSending: false,
      activeAssistantId: "",
    }
    this._messagesContainer = null
    this._messageElements = new Map()
    this._loadingElement = null
  }

  connectedCallback() {
    if (!this.querySelector(".sg-chat-messages")) {
      this.innerHTML = trustedHtml(`
        <div
          class="sg-chat-messages chat-scrollbar sg-chat-messages-panel"
          role="log"
          aria-label="Chatverlauf"
          aria-live="polite"
          aria-relevant="additions text"
        ></div>
      `)
    }
    this._messagesContainer = this.querySelector(".sg-chat-messages")
    this.render()
  }

  disconnectedCallback() {
    this._messagesContainer = null
    this._messageElements.clear()
    this._loadingElement = null
  }

  setState(nextState = {}) {
    this._state = { ...this._state, ...nextState }
    this.render()
  }

  addMessagesScrollListener(handler, options = { passive: true }) {
    this._messagesContainer?.addEventListener("scroll", handler, options)
  }

  removeMessagesScrollListener(handler, options = { passive: true }) {
    this._messagesContainer?.removeEventListener("scroll", handler, options)
  }

  isMessagesNearBottom(threshold = 8) {
    const container = this._messagesContainer
    if (!container) {
      return true
    }

    return container.scrollHeight - container.scrollTop - container.clientHeight <= threshold
  }

  scrollMessagesToBottom(behavior = "smooth") {
    const container = this._messagesContainer
    if (!container) {
      return
    }

    container.scrollTo({ top: container.scrollHeight, behavior })
  }

  observeMessagesResize(callback) {
    const container = this._messagesContainer
    if (!container) {
      return null
    }

    const observer = new ResizeObserver(callback)
    observer.observe(container)
    return observer
  }

  observeMessagesMutations(callback) {
    const container = this._messagesContainer
    if (!container) {
      return null
    }

    const observer = new MutationObserver(callback)
    observer.observe(container, {
      childList: true,
      subtree: true,
      characterData: true,
    })
    return observer
  }

  syncMessages() {
    const container = this._messagesContainer
    if (!container) {
      return
    }

    const nextMessageElements = new Map()

    const loadingAnchor = this._loadingElement?.parentNode === container ? this._loadingElement : null
    for (const [index, message] of this._state.messages.entries()) {
      const key = typeof message?.id === "string" && message.id ? `id:${message.id}` : `index:${index}:${message?.role || ""}`
      const componentName = message?.id === "context-character" || message?.id === "context-scene" ? "sg-context-message" : "sg-message"
      const renderedMessage = {
        ...message,
        showTypingDots:
          message?.role === "assistant" &&
          message?.id === this._state.activeAssistantId &&
          (!message?.content || !String(message.content).trim()),
      }
      let element = this._messageElements.get(key)

      if (element && element.localName !== componentName) {
        element.remove()
        element = null
      }

      if (!element) {
        element = document.createElement(componentName)
      }

      element.message = renderedMessage

      const referenceNode = container.children[index] || loadingAnchor || null
      if (referenceNode !== element) {
        container.insertBefore(element, referenceNode)
      }

      nextMessageElements.set(key, element)
    }

    this._messageElements.forEach((element, key) => {
      if (!nextMessageElements.has(key)) {
        element.remove()
      }
    })

    this._messageElements = nextMessageElements
  }

  syncLoadingPlaceholder() {
    const container = this._messagesContainer
    if (!container) {
      return
    }

    const shouldShowLoading = this._state.isSending && !this._state.activeAssistantId
    if (!shouldShowLoading) {
      this._loadingElement?.remove()
      this._loadingElement = null
      return
    }

    if (!this._loadingElement) {
      this._loadingElement = document.createElement("div")
      this._loadingElement.className = "msg-loading msg-bubble msg-bubble-standard"
      this._loadingElement.textContent = "Antwort wird erzeugt..."
    }

    if (this._loadingElement.parentNode !== container) {
      container.appendChild(this._loadingElement)
    }
  }

  render() {
    const container = this._messagesContainer
    if (!container) {
      return
    }

    this.syncMessages()
    this.syncLoadingPlaceholder()
  }
}

customElements.get("sg-chat") || customElements.define("sg-chat", SocialGameChat)
