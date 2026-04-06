import { trustedHtml } from "./trusted-types.js"

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
    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = trustedHtml(`
      <div class="msg-bubble msg-bubble-standard" hidden>
        <div class="msg-content">
          <div class="typing-dots"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>
          <div class="msg-body" hidden></div>
        </div>
        <div class="msg-timestamp" hidden></div>
      </div>
    `)

    this.$ = {
      bubble: this.querySelector(".msg-bubble"),
      typingDots: this.querySelector(".typing-dots"),
      body: this.querySelector(".msg-body"),
      timestamp: this.querySelector(".msg-timestamp"),
    }
  }

  set message(value) {
    this._message = value
    this.render()
  }

  render() {
    const message = this._message
    const formattedTimestamp = formatTimestamp(message.timestamp)

    this.$.timestamp.hidden = !formattedTimestamp
    this.$.timestamp.className = formattedTimestamp
      ? `msg-timestamp ${message.role === "user" ? "msg-timestamp-user msg-time-user" : "msg-timestamp-assistant msg-time-assistant"}`
      : "msg-timestamp"
    this.$.timestamp.textContent = formattedTimestamp

    this.$.bubble.className = `msg-bubble msg-bubble-standard ${message.role === "user" ? "msg-user msg-bubble-user-align" : "msg-assistant"}`
    this.$.bubble.hidden = false

    if (message.showTypingDots) {
      this.$.typingDots.hidden = false
      this.$.body.hidden = true
      return
    }

    this.$.typingDots.remove()
    this.$.body.hidden = false
    this.$.body.className = "msg-body msg-content-prewrap"
    this.$.body.textContent = message.content
  }
}

customElements.get("sg-message") || customElements.define("sg-message", SocialGameMessage)
