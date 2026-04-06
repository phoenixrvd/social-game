export class SocialGameContextMessage extends HTMLElement {
  constructor(message = null) {
    super()
    this._message = message
    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = `
      <div class="context-rich msg-context msg-bubble msg-bubble-context">
        <div class="sg-initial-context-html"></div>
      </div>
    `

    this.$ = {
      initialContextHtml: this.querySelector(".sg-initial-context-html"),
    }
  }

  set message(value) {
    this._message = value
    this.render()
  }

  render() {
    this.$.initialContextHtml.innerHTML = this._message?.html || ""
  }
}

customElements.get("sg-context-message") || customElements.define("sg-context-message", SocialGameContextMessage)
