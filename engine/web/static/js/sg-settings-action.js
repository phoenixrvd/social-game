class SocialGameSettingsAction extends HTMLElement {
  static get observedAttributes() {
    return ["aria-label", "aria-pressed", "disabled"]
  }

  constructor() {
    super()
    this.$ = {}
  }

  get disabled() {
    return this.hasAttribute("disabled")
  }

  set disabled(value) {
    this.toggleAttribute("disabled", Boolean(value))
  }

  connectedCallback() {
    const iconNode = this.querySelector('[slot="icon"]')
    const descriptionNode = this.querySelector('[slot="description"]')
    const titleNode = Array.from(this.children).find((node) => !node.hasAttribute("slot"))

    const iconMarkup = this._getIconMarkup(iconNode)
    const titleMarkup = titleNode ? titleNode.innerHTML : ""
    const descriptionMarkup = descriptionNode ? descriptionNode.innerHTML : ""
    const iconDataElement = iconNode?.getAttribute("data-element")
    const iconDataElementAttr = iconDataElement ? ` data-element="${iconDataElement}"` : ""

    this.innerHTML = /*html*/ `
      <button type="button" class="sg-settings-action-button">
        <span class="sg-settings-action-icon"${iconDataElementAttr}>${iconMarkup}</span>
        <span class="sg-settings-action-copy">
          <span class="sg-settings-action-title">${titleMarkup}</span>
          <span class="sg-settings-action-text">${descriptionMarkup}</span>
        </span>
      </button>
    `

    this.$ = {
      button: this.querySelector(".sg-settings-action-button"),
    }

    this._syncButtonAttributes()
  }

  attributeChangedCallback() {
    if (!this.isConnected || !this.$.button) {
      return
    }
    this._syncButtonAttributes()
  }

  _syncButtonAttributes() {
    const button = this.$.button

    button.disabled = this.disabled
    this._syncOptionalAttribute(button, "aria-label")
    this._syncOptionalAttribute(button, "aria-pressed")
  }

  _syncOptionalAttribute(target, name) {
    if (this.hasAttribute(name)) {
      target.setAttribute(name, this.getAttribute(name))
      return
    }

    target.removeAttribute(name)
  }

  _getIconMarkup(iconNode) {
    if (!iconNode) {
      return ""
    }

    if (iconNode.localName === "svg") {
      return iconNode.outerHTML
    }

    return iconNode.innerHTML
  }
}

customElements.get("sg-settings-action") || customElements.define("sg-settings-action", SocialGameSettingsAction)
