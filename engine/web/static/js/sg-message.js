import { appStore } from "./app-store.js"

function formatTimestamp(timestamp) {
  if (!timestamp) {
    return ""
  }

  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) {
    return timestamp
  }

  return new Intl.DateTimeFormat("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

class SocialGameMessage extends HTMLElement {
  constructor() {
    super()
    this._message = null
    this._state = {
      isAssistantTyping: false,
    }
    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = `
      <div class="msg-bubble msg-bubble-standard sg-hidden">
        <div class="msg-content">
          <div class="typing-dots sg-hidden"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>
          <div class="msg-body sg-hidden"></div>
        </div>
        <div class="msg-timestamp sg-hidden"></div>
      </div>
    `

    this.$ = {
      bubble: this.querySelector(".msg-bubble"),
      typingDots: this.querySelector(".typing-dots"),
      body: this.querySelector(".msg-body"),
      timestamp: this.querySelector(".msg-timestamp"),
    }

    const subscriptions = [
      ["isAssistantTyping", this.onAssistantTypingChanged.bind(this)],
    ]

    for (const [key, listener] of subscriptions) {
      appStore.subscribe(key, listener)
    }

    this.render()
  }

  onAssistantTypingChanged(isAssistantTyping) {
    this._state.isAssistantTyping = Boolean(isAssistantTyping)
    this.render()
  }

  set message(value) {
    this._message = value
    this.render()
  }

  isAssistantTypingMessage(message) {
    if (message?.role !== "assistant" || !this._state.isAssistantTyping) {
      return false
    }
    return !String(message.content || "").trim()
  }

  render() {
    const message = this._message
    if (!message || !this.$.bubble) {
      return
    }
    const formattedTimestamp = formatTimestamp(message.timestamp)

    this.$.timestamp.className = formattedTimestamp
      ? `msg-timestamp ${message.role === "user" ? "msg-timestamp-user msg-time-user" : "msg-timestamp-assistant msg-time-assistant"}`
      : "msg-timestamp"
    this.$.timestamp.classList.toggle("sg-hidden", !formattedTimestamp)
    this.$.timestamp.textContent = formattedTimestamp

    this.$.bubble.className = `msg-bubble msg-bubble-standard ${message.role === "user" ? "msg-user msg-bubble-user-align" : "msg-assistant"}`
    this.$.bubble.classList.remove("sg-hidden")

    if (this.isAssistantTypingMessage(message)) {
      this.$.typingDots.classList.remove("sg-hidden")
      this.$.body.classList.add("sg-hidden")
      return
    }

    this.$.typingDots.classList.add("sg-hidden")
    this.$.body.classList.remove("sg-hidden")
    this.$.body.className = "msg-body msg-content-prewrap"
    this.$.body.textContent = message.content
  }
}

customElements.get("sg-message") || customElements.define("sg-message", SocialGameMessage)
