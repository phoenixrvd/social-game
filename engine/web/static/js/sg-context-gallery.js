import "./sg-context-gallery-item.js"
import {appStore} from "./app-store.js"
import {appActions} from "./app-actions.js"

const PLUS_ICON = /*html*/ `
  <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
`

class SocialGameContextGallery extends HTMLElement {
  constructor() {
    super()
    this._state = {
      items: [],
      selectedId: "",
      playingVideoItemId: "",
      disabled: false,
      isOpen: false,
    }
    this.$ = {}
    this._hasInitialOpenScrollRun = false
  }

  connectedCallback() {
    const contextType = this.dataset.contextType || "npc"

    this.innerHTML = /*html*/ `
      <div class="sg-context-gallery-label-wrap">
        <span class="sg-selector-legend">${contextType === "scene" ? "SZENE" : "NPC"}</span>
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
    this.renderItems()
    this.updateSelectedItemState()
  }

  onSelectedIdChanged(selectedId) {
    this._state.selectedId = typeof selectedId === "string" ? selectedId : ""
    if (this._state.playingVideoItemId && this._state.playingVideoItemId !== this._state.selectedId) {
      this._state.playingVideoItemId = ""
    }
    this.updateSelectedItemState()
  }

  onDisabledTriggerChanged() {
    const state = appStore.getState()
    this._state.disabled = Boolean(state.isSending) || Boolean(state.isSessionLoading)
    this.$.fieldset.disabled = this._state.disabled
  }

  onPanelOpenChanged(isOpen) {
    this._state.isOpen = Boolean(isOpen)
    if (!this._state.isOpen || this._hasInitialOpenScrollRun) return
    this.scrollSelectedIntoViewOnFirstOpen()
  }

  render() {
    this.renderItems()
    this.$.fieldset.disabled = this._state.disabled

    if (this._state.isOpen && !this._hasInitialOpenScrollRun) {
      this.scrollSelectedIntoViewOnFirstOpen()
    }
  }

  renderItems() {
    const existingItems = new Map(
      Array.from(this.$.scroll.querySelectorAll("sg-context-gallery-item"))
        .map((el) => [el.dataset.itemId, el])
    )

    const rendered = this._state.items.map((item) => {
      const el = existingItems.get(item.id) || this.createGalleryItem(item.id)
      el.update({ imageUrl: item.image_url || "", label: item.label || "", videoUrl: item.video_url || "" })
      this._syncVideoElement(el, item.video_url || "")
      return el
    })

    const createButton = this.getOrCreateCreateButton()
    this.$.scroll.replaceChildren(...rendered, createButton)
    this.updateSelectedItemState()
  }

  createGalleryItem(itemId) {
    const el = document.createElement("sg-context-gallery-item")
    el.dataset.itemId = itemId
    el.className = "sg-context-gallery-item"
    el.setAttribute("type", "button")
    el.setAttribute("aria-pressed", "false")
    el.innerHTML = /*html*/ `
      <span class="sg-context-gallery-media">
        <img class="sg-context-gallery-image" src="" alt="" loading="eager" />
      </span>
      <span class="sg-context-gallery-label"></span>
    `
    el.addEventListener("click", (e) => {
      if (this._state.disabled) return
      const state = appStore.getState()
      const selectedId = typeof state[this._stateKey] === "string" ? state[this._stateKey] : ""
      const clickedMedia = Boolean(e.target.closest(".sg-context-gallery-media"))
      const videoUrl = e.currentTarget.getAttribute("data-video-url")
      if (clickedMedia && videoUrl) {
        this.playItemVideo(e.currentTarget)
      } else if (this._state.playingVideoItemId !== itemId) {
        this._state.playingVideoItemId = ""
      }
      if (itemId !== selectedId) {
        this.handleItemClick(itemId)
      }
    })
    return el
  }

  getOrCreateCreateButton() {
    const existing = this.$.scroll.querySelector(".sg-context-gallery-create")
    if (existing) return existing

    const label = this._contextType === "scene" ? "Szene erstellen" : "NPC erstellen"
    const template = document.createElement("template")
    template.innerHTML = /*html*/ `
      <button
        type="button"
        class="sg-context-gallery-item sg-context-gallery-create sg-context-gallery-create-scene"
        title="${label}"
        aria-label="${label}"
      >
        <div class="sg-context-gallery-image sg-context-gallery-create-scene-image">
          ${PLUS_ICON}
        </div>
        <span class="sg-context-gallery-label">${label}</span>
      </button>
    `.trim()

    const button = template.content.firstElementChild
    button.addEventListener("click", () => {
      if (!this._state.disabled) {
        const eventName = this._contextType === "scene" ? "createSceneRequested" : "createNpcRequested"
        this.dispatchEvent(new CustomEvent(eventName))
      }
    })
    return button
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
  }

  _syncVideoElement(el, videoUrl) {
    const media = el.querySelector(".sg-context-gallery-media")
    if (!media) return

    const hasVideo = typeof videoUrl === "string" && videoUrl.trim().length > 0
    let video = media.querySelector("video")

    if (hasVideo) {
      el.setAttribute("data-video-url", videoUrl)
      if (!video) {
        const tpl = document.createElement("template")
        tpl.innerHTML = /*html*/ `<video
          class="sg-context-gallery-video"
          preload="auto"
          muted
          playsinline
          disablepictureinpicture
          disableremoteplayback
          loading="eager"
        ></video>`
        video = tpl.content.firstElementChild
        media.appendChild(video)
      }
      video.muted = true
      video.defaultMuted = true
      if (video.getAttribute("src") !== videoUrl) video.src = videoUrl
    } else {
      el.removeAttribute("data-video-url")
      if (video) video.remove()
    }
  }

  playItemVideo(el) {
    const video = el.querySelector("video")
    if (!video) return
    video.muted = true
    video.defaultMuted = true
    this._state.playingVideoItemId = el.dataset.itemId || ""
    video.classList.add("sg-context-gallery-video--playing")
    video.currentTime = 0
    video.play().catch(() => {})
  }

  updateSelectedItemState() {
    this.syncSelectedItemClass()
  }

  syncSelectedItemClass() {
    for (const el of this.$.scroll.querySelectorAll("sg-context-gallery-item")) {
      el.selected = el.dataset.itemId === this._state.selectedId
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
}

customElements.get("sg-context-gallery") || customElements.define("sg-context-gallery", SocialGameContextGallery)
