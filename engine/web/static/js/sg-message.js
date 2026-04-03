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

class SocialGameMessage extends HTMLElement {
  constructor() {
    super()
    this._message = null
    this._messageSnapshot = null
  }

  connectedCallback() {
    this.render()
  }

  createMessageSnapshot(message) {
    if (!message || typeof message !== "object") {
      return null
    }

    return {
      id: typeof message.id === "string" ? message.id : "",
      role: typeof message.role === "string" ? message.role : "",
      content: typeof message.content === "string" ? message.content : "",
      timestamp: typeof message.timestamp === "string" ? message.timestamp : "",
      html: typeof message.html === "string" ? message.html : "",
      showTypingDots: Boolean(message.showTypingDots),
    }
  }

  isSameMessageSnapshot(left, right) {
    if (!left || !right) {
      return left === right
    }

    return left.id === right.id &&
      left.role === right.role &&
      left.content === right.content &&
      left.timestamp === right.timestamp &&
      left.html === right.html &&
      left.showTypingDots === right.showTypingDots
  }

  set message(value) {
    const nextMessage = value && typeof value === "object" ? value : null
    const nextSnapshot = this.createMessageSnapshot(nextMessage)

    if (this.isSameMessageSnapshot(this._messageSnapshot, nextSnapshot)) {
      return
    }

    this._message = nextMessage
    this._messageSnapshot = nextSnapshot
    this.render()
  }

  render() {
    const message = this._message
    if (!message) {
      this.innerHTML = trustedHtml("")
      return
    }

    const wrapperClassName = [
      "msg-bubble msg-bubble-standard",
      message.role === "user" ? "msg-user msg-bubble-user-align" : "msg-assistant",
    ]
      .filter(Boolean)
      .join(" ")

    const showTypingDots = Boolean(message.showTypingDots)
    const formattedTimestamp = formatTimestamp(message.timestamp)

    let contentMarkup
    if (showTypingDots) {
      contentMarkup = '<div class="typing-dots"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>'
    } else if (typeof message.html === "string" && message.html.trim()) {
      contentMarkup = sanitizeMessageHtml(message.html)
    } else {
      contentMarkup = `<div class="msg-content-prewrap">${escapeHtml(message.content)}</div>`
    }

    const timestampMarkup = formattedTimestamp
      ? `<div class="${[
          "msg-timestamp",
          message.role === "user" ? "msg-timestamp-user msg-time-user" : "msg-timestamp-assistant msg-time-assistant",
        ].join(" ")}">${escapeHtml(formattedTimestamp)}</div>`
      : ""

    this.innerHTML = trustedHtml(`
      <div class="${wrapperClassName}">
        ${contentMarkup}
        ${timestampMarkup}
      </div>
    `)
  }
}

customElements.get("sg-message") || customElements.define("sg-message", SocialGameMessage)
