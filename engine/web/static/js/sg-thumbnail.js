import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"

function isMobileViewport() {
  return window.matchMedia("(max-width: 1023px)").matches
}

class SocialGameThumbnail extends HTMLElement {
  constructor() {
    super()
    this._state = {
      imageUrl: "",
      imageSignature: "",
      isLoading: false,
      isExpanded: false,
      videoUrl: "",
      imageIsOriginal: true,
      imageVideoAutoplayRequestedAt: null,
    }

    this.$ = {}
    this._lastFocusedElement = null
    this._lastAnimatedSignature = ""
    this._inlineVideoActive = false
    this._updatedClassTimer = null
  }

  connectedCallback() {
    this.innerHTML = this.buildMarkup()
    this.cacheElements()
    this.registerDomEvents()
    this.registerSubscriptions()
    this.syncFromStore()
    this.syncVideoSources()
    this.render()
  }

  buildMarkup() {
    return /*html*/ `
      <div class="sg-image-frame">
        <div class="sg-image-content">
          <img class="sg-image-bg" src="data:," alt="Hintergrund" loading="lazy" decoding="async" fetchpriority="low" />
          <img class="sg-image-main" src="data:," alt="Szenenbild" role="button" tabindex="0" aria-label="Bild vergroessern" loading="lazy" decoding="async" />
          <video class="sg-image-inline-video" preload="auto" muted playsinline disablepictureinpicture disableremoteplayback></video>
        </div>
      </div>

      <div class="sg-image-overlay" role="dialog" aria-modal="true" aria-label="Vergroessertes Szenenbild" tabindex="-1">
        <div class="sg-image-overlay-frame">
          <img class="sg-image-overlay-bg" src="data:," alt="Hintergrund" loading="lazy" decoding="async" />
          <img class="sg-image-overlay-main" src="data:," alt="Szenenbild" loading="lazy" decoding="async" />
          <video class="sg-image-overlay-video" preload="auto" muted playsinline disablepictureinpicture disableremoteplayback></video>
        </div>
      </div>
    `
  }

  cacheElements() {
    this.$ = {
      frame: this.querySelector(".sg-image-frame"),
      overlay: this.querySelector(".sg-image-overlay"),
      overlayFrame: this.querySelector(".sg-image-overlay-frame"),
      bg: this.querySelector(".sg-image-bg"),
      main: this.querySelector(".sg-image-main"),
      inlineVideo: this.querySelector(".sg-image-inline-video"),
      overlayBg: this.querySelector(".sg-image-overlay-bg"),
      overlayMain: this.querySelector(".sg-image-overlay-main"),
      overlayVideo: this.querySelector(".sg-image-overlay-video"),
    }
  }

  registerDomEvents() {
    this.$.main.addEventListener("error", this.handleMainError.bind(this))
    this.$.main.addEventListener("click", this.handleMainClick.bind(this))
    this.$.main.addEventListener("keydown", this.handleMainKeyDown.bind(this))
    this.$.inlineVideo.addEventListener("click", this.handleInlineVideoClick.bind(this))
    this.$.overlay.addEventListener("click", this.handleOverlayClick.bind(this))
    this.$.overlay.addEventListener("keydown", this.handleOverlayKeyDown.bind(this))
  }

  registerSubscriptions() {
    appStore.subscribeState(this.onStateChanged.bind(this))
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.imageUrl = typeof state.imageUrl === "string" ? state.imageUrl : ""
    this._state.imageSignature = typeof state.imageSignature === "string" ? state.imageSignature : ""
    this._state.isExpanded = Boolean(state.isImageExpanded)
    this._state.isLoading = Boolean(state.isImageRefreshLoading)
    this._state.videoUrl = typeof state.videoUrl === "string" ? state.videoUrl : ""
    this._state.imageIsOriginal = typeof state.imageIsOriginal === "boolean" ? state.imageIsOriginal : true
    this._state.imageVideoAutoplayRequestedAt = state.imageVideoAutoplayRequestedAt || null
  }

  onStateChanged(state, prevState, changedKeys) {
    if (!this.hasRelevantChange(changedKeys)) {
      return
    }

    const imageUrlChanged = prevState.imageUrl !== state.imageUrl
    const videoSourceChanged = prevState.videoUrl !== state.videoUrl || prevState.imageIsOriginal !== state.imageIsOriginal
    const autoplayRequested = prevState.imageVideoAutoplayRequestedAt !== state.imageVideoAutoplayRequestedAt
    const shouldRender = this.hasRenderChange(changedKeys)

    this.syncFromStore()

    if (imageUrlChanged && !this.hasActiveVideo()) {
      this._inlineVideoActive = false
    }

    if (videoSourceChanged) {
      this.syncVideoSources()
    }

    if (shouldRender) {
      this.render()
    }

    if (autoplayRequested && !imageUrlChanged && this._state.imageVideoAutoplayRequestedAt) {
      this.playInlineVideoFromImageUpdate()
    }
  }

  hasRelevantChange(changedKeys) {
    return this.hasRenderChange(changedKeys) || changedKeys.includes("imageVideoAutoplayRequestedAt")
  }

  hasRenderChange(changedKeys) {
    return changedKeys.some((key) =>
      ["imageUrl", "imageSignature", "isImageExpanded", "isImageRefreshLoading", "videoUrl", "imageIsOriginal"].includes(key)
    )
  }

  syncVideoSources() {
    ;[this.$.inlineVideo, this.$.overlayVideo].forEach((video) => {
      video.muted = true
      video.defaultMuted = true
      if (this._state.videoUrl && this._state.imageIsOriginal) {
        if (video.getAttribute("src") !== this._state.videoUrl) {
          video.src = this._state.videoUrl
          video.load()
        }
      } else {
        video.removeAttribute("src")
        video.load()
      }
    })
  }

  handleMainError(event) {
    event.stopPropagation()
    this.$.main.classList.remove("is-updated")
    this.$.overlayMain.classList.remove("is-updated")
    appActions.setImageError()
  }

  shouldAnimateImageUpdate() {
    const signature = this._state.imageSignature
    if (!signature || signature === this._lastAnimatedSignature) {
      return false
    }

    this._lastAnimatedSignature = signature
    return true
  }

  playImageUpdateAnimation() {
    this.$.main.classList.add("is-updated")
    this.$.inlineVideo.classList.add("is-updated")
    this.$.overlayMain.classList.add("is-updated")

    if (this._updatedClassTimer !== null) {
      window.clearTimeout(this._updatedClassTimer)
    }

    this._updatedClassTimer = window.setTimeout(() => {
      this.$.main.classList.remove("is-updated")
      this.$.inlineVideo.classList.remove("is-updated")
      this.$.overlayMain.classList.remove("is-updated")
      this._updatedClassTimer = null
    }, 520)
  }

  handleMainClick(event) {
    event.stopPropagation()
    if (this.playInlineVideoFromUserGesture()) {
      return
    }
    this.requestExpandFromUserGesture()
  }

  handleMainKeyDown(event) {
    if (event.key !== "Enter" && event.key !== " ") {
      return
    }

    event.preventDefault()
    if (this.playInlineVideoFromUserGesture()) {
      return
    }
    this.requestExpandFromUserGesture()
  }

  handleInlineVideoClick(event) {
    event.stopPropagation()
    this.playInlineVideoFromUserGesture()
  }

  _playInlineVideo() {
    this._inlineVideoActive = true
    this.renderInlineVideo(Boolean(this._state.imageUrl))
    this.$.inlineVideo.pause()
    this.$.inlineVideo.currentTime = 0
    this.$.inlineVideo.play().catch(() => {})
  }

  playInlineVideoFromUserGesture() {
    if (!this.hasActiveVideo() || isMobileViewport()) {
      return false
    }

    this._playInlineVideo()
    return true
  }

  playInlineVideoFromImageUpdate() {
    if (!this.hasActiveVideo() || isMobileViewport()) {
      return
    }

    this._playInlineVideo()
  }

  hasActiveVideo() {
    return Boolean(this._state.videoUrl && this._state.imageIsOriginal)
  }

  handleOverlayClick() {
    if (!this._state.isExpanded) {
      return
    }

    this.requestCollapseFromUserGesture()
  }

  handleOverlayKeyDown(event) {
    if (event.key !== "Escape") {
      return
    }

    event.preventDefault()
    this.requestCollapseFromUserGesture()
  }

  requestExpandFromUserGesture() {
    if (!this.canOpenOverlay()) {
      return
    }

    this._lastFocusedElement = document.activeElement
    appActions.toggleImageExpand(true)
  }

  requestCollapseFromUserGesture() {
    appActions.toggleImageExpand(false)
    this.restoreFocus()
  }

  canOpenOverlay() {
    return Boolean(this._state.imageUrl && isMobileViewport())
  }

  restoreFocus() {
    if (this._lastFocusedElement instanceof HTMLElement) {
      this._lastFocusedElement.focus()
    }
  }

  render() {
    const hasImage = typeof this._state.imageUrl === "string" && this._state.imageUrl.trim().length > 0
    const overlayIsOpen = Boolean(isMobileViewport() && this._state.isExpanded && hasImage)
    const showLoadingState = Boolean(this._state.isLoading && hasImage)
    const isSceneThumbnail = this.classList.contains("sg-scene-thumbnail")

    this.$.frame.classList.toggle("sg-hidden", !hasImage)
    this.$.frame.classList.toggle("is-loading", showLoadingState && !isSceneThumbnail)
    this.$.overlay.classList.toggle("is-open", overlayIsOpen)

    if (overlayIsOpen) {
      this.$.overlay.focus()
    }

    this.renderInlineVideo(hasImage)
    this.renderOverlayVideo(overlayIsOpen)

    if (!hasImage) {
      return
    }

    const currentSrc = this.$.main.getAttribute("src") || ""
    if (currentSrc === this._state.imageUrl) {
      return
    }

    const shouldAnimate = this.shouldAnimateImageUpdate()

    if (shouldAnimate) {
      this.playImageUpdateAnimationAfterLoad(this._state.imageUrl)
    }

    ;[this.$.bg, this.$.main, this.$.overlayBg, this.$.overlayMain].forEach((img) => {
      img.src = this._state.imageUrl
    })
  }

  playImageUpdateAnimationAfterLoad(imageUrl) {
    this.$.main.addEventListener(
      "load",
      () => {
        if (this.$.main.getAttribute("src") !== imageUrl) {
          return
        }

        this.playImageUpdateAnimation()
        this.playInlineVideoFromImageUpdate()
      },
      { once: true }
    )
  }

  renderOverlayVideo(overlayIsOpen) {
    const videoActive = this.hasActiveVideo()
    const video = this.$.overlayVideo

    this.$.overlayMain.classList.toggle("sg-hidden", videoActive && overlayIsOpen)
    video.classList.toggle("is-visible", videoActive && overlayIsOpen)

    if (videoActive && overlayIsOpen) {
      if (video.paused) {
        video.play().catch(() => {})
      }
    } else {
      if (!video.paused) {
        video.pause()
      }
    }
  }

  renderInlineVideo(hasImage) {
    const videoActive = Boolean(hasImage && this._inlineVideoActive && this.hasActiveVideo() && !isMobileViewport())
    const video = this.$.inlineVideo

    this.$.main.classList.toggle("sg-hidden", videoActive)
    video.classList.toggle("is-visible", videoActive)

    if (!videoActive && !video.paused) {
      video.pause()
    }
  }
}

customElements.get("sg-thumbnail") || customElements.define("sg-thumbnail", SocialGameThumbnail)
