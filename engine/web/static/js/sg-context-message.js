import { PENCIL_ICON } from "./icons.js"

export class SocialGameContextMessage extends HTMLElement {
  constructor(message = null) {
    super()
    this._message = message
    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = /*html*/ `
      <div class="context-rich msg-context msg-bubble msg-bubble-context">
        <div class="sg-initial-context-html"></div>
        <div class="sg-context-message-actions sg-hidden">
          <button type="button" class="sg-context-message-edit" aria-label="Scene Context bearbeiten">
            ${PENCIL_ICON}
          </button>
        </div>
      </div>
    `

    this.$ = {
      actions: this.querySelector(".sg-context-message-actions"),
      editButton: this.querySelector(".sg-context-message-edit"),
      initialContextHtml: this.querySelector(".sg-initial-context-html"),
    }

    this.$.editButton.addEventListener("click", this.onEditClicked.bind(this))
  }

  onEditClicked() {
    this.dispatchEvent(new CustomEvent("editSceneContextRequested", { bubbles: true, composed: true }))
  }

  set message(value) {
    this._message = value
    this.render()
  }

  render() {
    const isEditableSceneContext = Boolean(this._message?.is_editable_scene_context)
    this.$.actions.classList.toggle("sg-hidden", !isEditableSceneContext)
    this.$.initialContextHtml.innerHTML = this._message?.html || ""
  }
}

customElements.get("sg-context-message") || customElements.define("sg-context-message", SocialGameContextMessage)
