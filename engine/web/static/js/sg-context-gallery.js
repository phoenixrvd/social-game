import { appStore } from "./app-store.js"
import { appActions } from "./app-actions.js"

class SocialGameContextGallery extends HTMLElement {
  constructor() {
    super()
    this._state = {
      items: [],
      selectedId: "",
      disabled: false,
      isOpen: false,
    }
    this.$ = {}
    this._hasInitialOpenScrollRun = false
  }

  connectedCallback() {
    const data = {
      contextType: this.dataset.contextType || "npc",
    }

    const contextType = data.contextType

    this.innerHTML = `
      <div class="sg-context-gallery-label-wrap">
        <span class="sg-selector-legend">${this._getLegendLabel(contextType)}</span>
      </div>
      <fieldset class="sg-context-gallery-fieldset">
        <div class="sg-context-gallery-scroll"></div>
      </fieldset>
    `

    this.$ = {
      scroll: this.querySelector(".sg-context-gallery-scroll"),
      fieldset: this.querySelector(".sg-context-gallery-fieldset"),
    }

    this._contextType = contextType
    this._stateKey = contextType === "scene" ? "sceneId" : "npcId"
    this._itemsKey = contextType === "scene" ? "scenes" : "npcs"

    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  registerSubscriptions() {
    const subscriptions = [
      [this._itemsKey, this.onItemsChanged.bind(this)],
      [this._stateKey, this.onSelectedIdChanged.bind(this)],
      ["isSending", this.onDisabledTriggerChanged.bind(this)],
      ["isSessionLoading", this.onDisabledTriggerChanged.bind(this)],
      ["isSelectorPanelOpen", this.onPanelOpenChanged.bind(this)],
    ]

    for (const [key, listener] of subscriptions) {
      appStore.subscribe(key, listener)
    }
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.items = Array.isArray(state[this._itemsKey]) ? state[this._itemsKey] : []
    this._state.selectedId = typeof state[this._stateKey] === "string" ? state[this._stateKey] : ""
    this._state.disabled = Boolean(state.isSending) || Boolean(state.isSessionLoading)
    this._state.isOpen = Boolean(state.isSelectorPanelOpen)
  }

  onItemsChanged(items) {
    this._state.items = Array.isArray(items) ? items : []
    this.render()
  }

  onSelectedIdChanged(selectedId) {
    this._state.selectedId = typeof selectedId === "string" ? selectedId : ""
    this.render()
  }

  onDisabledTriggerChanged() {
    const state = appStore.getState()
    this._state.disabled = Boolean(state.isSending) || Boolean(state.isSessionLoading)
    this.render()
  }

  onPanelOpenChanged(isOpen) {
    this._state.isOpen = Boolean(isOpen)
    if (!this._state.isOpen || this._hasInitialOpenScrollRun) return

    this.scrollSelectedIntoViewOnFirstOpen()
  }

  handleItemClick(itemId) {
    if (this._state.disabled || typeof itemId !== "string" || !itemId) return

    const state = appStore.getState()
    const selectedId = typeof state[this._stateKey] === "string" ? state[this._stateKey] : ""
    if (itemId === selectedId) return

    const session = this._contextType === "scene"
      ? { npc_id: state.npcId, scene_id: itemId }
      : { npc_id: itemId, scene_id: state.sceneId }

    appActions.updateSession(session)

    if (state.isSelectorPanelOpen) {
      appActions.toggleSelectorPanel()
    }
  }

  render() {
    this.$.scroll.innerHTML = this._state.items
      .map((item) => this._renderItem(item))
      .join("")

    this.$.scroll.querySelectorAll(".sg-context-gallery-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        const itemId = e.currentTarget.getAttribute("data-item-id")
        this.handleItemClick(itemId)
      })
    })

    this.$.fieldset.disabled = this._state.disabled

    if (this._state.isOpen && !this._hasInitialOpenScrollRun) {
      this.scrollSelectedIntoViewOnFirstOpen()
    }
  }

  scrollSelectedIntoViewOnFirstOpen(attempt = 0) {
    if (this._hasInitialOpenScrollRun) return

    requestAnimationFrame(() => {
      if (this._hasInitialOpenScrollRun) return

      const didScroll = this.scrollSelectedIntoView()
      if (didScroll) {
        this._hasInitialOpenScrollRun = true
        return
      }

      if (attempt >= 8 || !this._state.isOpen) return
      setTimeout(() => this.scrollSelectedIntoViewOnFirstOpen(attempt + 1), 60)
    })
  }

  scrollSelectedIntoView() {
    if (!this.$.scroll) return false

    const selectedItem = this.$.scroll.querySelector(".sg-context-gallery-item--selected")
    if (!selectedItem) return false

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    const behavior = reduceMotion ? "auto" : "smooth"

    const container = this.$.scroll
    if (container.clientWidth <= 0) return false

    const maxLeft = Math.max(container.scrollWidth - container.clientWidth, 0)
    const centeredLeft = selectedItem.offsetLeft - (container.clientWidth - selectedItem.offsetWidth) / 2
    const targetLeft = Math.min(Math.max(centeredLeft, 0), maxLeft)

    container.scrollTo({ left: targetLeft, behavior })

    return true
  }

  _getLegendLabel(contextType) {
    return contextType === "scene" ? "SZENE" : "NPC"
  }

  _renderItem(item) {
    const isSelected = item.id === this._state.selectedId
    const selectedClass = isSelected ? " sg-context-gallery-item--selected" : ""
    const ariaPressed = isSelected ? "true" : "false"

    return `
      <button
        type="button"
        class="sg-context-gallery-item${selectedClass}"
        data-item-id="${item.id}"
        aria-pressed="${ariaPressed}"
        title="${item.label}"
      >
        <img
          class="sg-context-gallery-image"
          src="${item.image_url}"
          alt="${item.label}"
          loading="lazy"
        />
        <span class="sg-context-gallery-label">${item.label}</span>
      </button>
    `
  }
}

customElements.get("sg-context-gallery") || customElements.define("sg-context-gallery", SocialGameContextGallery)

