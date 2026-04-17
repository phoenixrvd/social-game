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
    this.innerHTML = `
      <div class="msg-bubble msg-bubble-standard sg-hidden">
        <div class="msg-content">
          <div class="msg-body msg-content-prewrap"></div>
        </div>
        <div class="msg-timestamp sg-hidden"></div>
      </div>
    `

    this.$ = {
      bubble: this.querySelector(".msg-bubble"),
      body: this.querySelector(".msg-body"),
      timestamp: this.querySelector(".msg-timestamp"),
    }

    this.render()
  }

  set message(value) {
    this._message = value
    this.render()
  }

  render() {
    const message = this._message
    if (!message) {
      return
    }

    const content = typeof message.content === "string" ? message.content : ""
    if (message.role === "assistant" && !content) {
      this.$.bubble.className = "msg-bubble msg-bubble-standard sg-hidden"
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
    this.$.body.textContent = content
  }
}

customElements.get("sg-message") || customElements.define("sg-message", SocialGameMessage)
