import "./sg-message.js"
import "./sg-context-message.js"
import { appStore } from "./app-store.js"

class SocialGameChat extends HTMLElement {
  constructor() {
    super()
    this._state = {
      messages: [],
    }
    this.$ = {
      messages: null,
    }
    this._messageElements = new Map()
  }

  connectedCallback() {
    this.innerHTML = `
      <div
        class="sg-chat-messages chat-scrollbar sg-chat-messages-panel"
        role="log"
        aria-label="Chatverlauf"
        aria-live="polite"
        aria-relevant="additions"
      ></div>
    `
    this.$.messages = this.querySelector(".sg-chat-messages")
    const subscriptions = [
      ["messages", this.onMessagesChanged.bind(this)],
    ]

    for (const [key, listener] of subscriptions) {
      appStore.subscribe(key, listener)
    }
  }

  onMessagesChanged(messages) {
    this._state.messages = Array.isArray(messages) ? messages : []
    this.render()
  }

  scrollMessagesToBottom(behavior = "smooth") {
    this.$.messages.scrollTo({ top: this.$.messages.scrollHeight, behavior })
  }

  syncMessages() {
    const container = this.$.messages
    const nextMessageElements = new Map()

    for (const [index, message] of this._state.messages.entries()) {
      const key = typeof message?.id === "string" && message.id ? `id:${message.id}` : `index:${index}:${message?.role || ""}`
      const contextMessageIds = ["context-character", "context-scene", "context-relationship"]
      const componentName = contextMessageIds.includes(message?.id) ? "sg-context-message" : "sg-message"
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
      element.message = message

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
