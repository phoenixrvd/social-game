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
    this.$ = {
      messages: null,
    }
    this._messageElements = new Map()
  }

  connectedCallback() {
    this.innerHTML = trustedHtml(`
      <div
        class="sg-chat-messages chat-scrollbar sg-chat-messages-panel"
        role="log"
        aria-label="Chatverlauf"
        aria-live="polite"
        aria-relevant="additions"
      ></div>
    `)
    this.$.messages = this.querySelector(".sg-chat-messages")
    this.render()
  }


  setState(nextState = {}) {
    this._state = { ...this._state, ...nextState }
    this.render()
  }

  scrollMessagesToBottom(behavior = "smooth") {
    this.$.messages.scrollTo({ top: this.$.messages.scrollHeight, behavior })
  }

  syncMessages() {
    const container = this.$.messages
    const nextMessageElements = new Map()
    const activeAssistantMessage = this._state.messages.find((message) => message?.id === this._state.activeAssistantId)
    const showTypingDotsForActiveAssistant =
      this._state.isSending &&
      activeAssistantMessage?.role === "assistant" &&
      (!activeAssistantMessage?.content || !String(activeAssistantMessage.content).trim())

    for (const [index, message] of this._state.messages.entries()) {
      const key = typeof message?.id === "string" && message.id ? `id:${message.id}` : `index:${index}:${message?.role || ""}`
      const componentName = message?.id === "context-character" || message?.id === "context-scene" ? "sg-context-message" : "sg-message"
      const renderedMessage = {
        ...message,
        showTypingDots: message?.id === this._state.activeAssistantId ? showTypingDotsForActiveAssistant : false,
      }
      let element = this._messageElements.get(key)

      if (element && element.localName !== componentName) {
        element.remove()
        element = null
      }

      if (!element) {
        element = document.createElement(componentName)
      }

      const referenceNode = container.children[index] || null
      if (referenceNode !== element) {
        container.insertBefore(element, referenceNode)
      }
      element.message = renderedMessage

      nextMessageElements.set(key, element)
    }

    this._messageElements.forEach((element, key) => {
      if (!nextMessageElements.has(key)) {
        element.remove()
      }
    })

    this._messageElements = nextMessageElements
  }

  render() {
    const hadMessages = this._messageElements.size > 0
    this.syncMessages()
    this.scrollMessagesToBottom(hadMessages ? "smooth" : "instant")
  }
}

customElements.get("sg-chat") || customElements.define("sg-chat", SocialGameChat)
