class SocialGameSettingsAction extends HTMLElement {
  static get observedAttributes() {
    return ["aria-label", "aria-pressed", "disabled"]
  }

  constructor() {
    super()
    this._isRendered = false
  }

  connectedCallback() {
    if (!this._isRendered) {
      this._render()
      this._isRendered = true
    }
    this._syncButtonAttributes()
  }

  attributeChangedCallback() {
    this._syncButtonAttributes()
  }

  get disabled() {
    return this.hasAttribute("disabled")
  }

  set disabled(value) {
    this.toggleAttribute("disabled", Boolean(value))
  }

  focus(options) {
    this._button()?.focus(options)
  }

  click() {
    this._button()?.click()
  }

  _button() {
    return this.querySelector(".sg-settings-action-button")
  }

  _render() {
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
  }

  _syncButtonAttributes() {
    const button = this._button()
    if (!button) {
      return
    }

    button.disabled = this.disabled

    if (this.hasAttribute("aria-label")) {
      button.setAttribute("aria-label", this.getAttribute("aria-label"))
    } else {
      button.removeAttribute("aria-label")
    }

    if (this.hasAttribute("aria-pressed")) {
      button.setAttribute("aria-pressed", this.getAttribute("aria-pressed"))
    } else {
      button.removeAttribute("aria-pressed")
    }
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
