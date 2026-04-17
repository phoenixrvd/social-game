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
    this._observedLastMessage = null
    this._lastMessageResizeObserver = new ResizeObserver(() => {
      this.scrollMessagesToBottom("instant")
    })
    this._hasRenderedMessages = false
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
      let isNewElement = false

      if (element && element.localName !== componentName) {
        element.remove()
        element = null
      }

      if (!element) {
        element = document.createElement(componentName)
        isNewElement = true
      }

      const referenceNode = container.children[index] || null
      if (referenceNode !== element) {
        container.insertBefore(element, referenceNode)
      }

      if (this.shouldAnimateMessage(componentName, isNewElement)) {
        element.classList.add("sg-message-enter")
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
    this._hasRenderedMessages = true
  }

  shouldAnimateMessage(componentName, isNewElement) {
    if (!this._hasRenderedMessages) {
      return false
    }
    return componentName === "sg-message" && isNewElement
  }

  disconnectLastMessageObserver() {
    if (!this._observedLastMessage) {
      return
    }
    this._lastMessageResizeObserver.unobserve(this._observedLastMessage)
    this._observedLastMessage = null
  }

  syncLastMessageObserver() {
    const nextLastMessage = this.$.messages.lastElementChild
    if (nextLastMessage === this._observedLastMessage) {
      return
    }

    this.disconnectLastMessageObserver()

    if (!nextLastMessage) {
      return
    }

    this._lastMessageResizeObserver.observe(nextLastMessage)
    this._observedLastMessage = nextLastMessage
  }

  render() {
    this.syncMessages()
    this.syncLastMessageObserver()
    this.scrollMessagesToBottom("instant")
  }
}

customElements.get("sg-chat") || customElements.define("sg-chat", SocialGameChat)
