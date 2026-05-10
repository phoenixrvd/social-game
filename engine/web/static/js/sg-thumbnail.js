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
      imageOriginalUrl: "",
      imageBackups: [],
      imageSignature: "",
      isLoading: false,
      isExpanded: false,
      overlayImageIndex: 0,
      videoUrl: "",
      imageIsOriginal: true,
      imageVideoAutoplayRequestedAt: null,
    }

    this.$ = {}
    this._lastFocusedElement = null
    this._lastAnimatedSignature = ""
    this._inlineVideoActive = false
    this._updatedClassTimer = null
    this._overlayTransitionTimer = null
    this._overlaySwipeStart = null
    this._suppressNextOverlayClick = false
    this._overlayPreloadedImages = new Map()
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
          <img class="sg-image-overlay-previous" src="data:," alt="" aria-hidden="true" loading="lazy" decoding="async" />
          <img class="sg-image-overlay-main" src="data:," alt="Szenenbild" loading="lazy" decoding="async" />
          <video class="sg-image-overlay-video" preload="auto" muted playsinline disablepictureinpicture disableremoteplayback></video>
          <button class="sg-image-overlay-nav sg-image-overlay-nav-left" type="button" aria-label="Vorheriges Bild anzeigen">&lsaquo;</button>
          <button class="sg-image-overlay-nav sg-image-overlay-nav-right" type="button" aria-label="Aelteres Bild anzeigen">&rsaquo;</button>
        </div>
      </div>
    `
  }

  cacheElements() {
    this.$ = {
      frame: this.querySelector(".sg-image-frame"),
      content: this.querySelector(".sg-image-content"),
      overlay: this.querySelector(".sg-image-overlay"),
      overlayFrame: this.querySelector(".sg-image-overlay-frame"),
      bg: this.querySelector(".sg-image-bg"),
      main: this.querySelector(".sg-image-main"),
      inlineVideo: this.querySelector(".sg-image-inline-video"),
      overlayBg: this.querySelector(".sg-image-overlay-bg"),
      overlayPrevious: this.querySelector(".sg-image-overlay-previous"),
      overlayMain: this.querySelector(".sg-image-overlay-main"),
      overlayVideo: this.querySelector(".sg-image-overlay-video"),
      overlayPreviousButton: this.querySelector(".sg-image-overlay-nav-left"),
      overlayNext: this.querySelector(".sg-image-overlay-nav-right"),
    }
  }

  registerDomEvents() {
    this.$.main.addEventListener("error", this.handleMainError.bind(this))
    this.$.content.addEventListener("click", this.handleContentClick.bind(this))
    this.$.main.addEventListener("click", this.handleMainClick.bind(this))
    this.$.main.addEventListener("keydown", this.handleMainKeyDown.bind(this))
    this.$.inlineVideo.addEventListener("click", this.handleInlineVideoClick.bind(this))
    this.$.overlay.addEventListener("click", this.handleOverlayClick.bind(this))
    this.$.overlay.addEventListener("keydown", this.handleOverlayKeyDown.bind(this))
    this.$.overlayFrame.addEventListener("pointerdown", this.handleOverlayPointerDown.bind(this))
    this.$.overlayFrame.addEventListener("pointerup", this.handleOverlayPointerUp.bind(this))
    this.$.overlayFrame.addEventListener("pointercancel", this.handleOverlayPointerCancel.bind(this))
    this.$.overlayPreviousButton.addEventListener("click", this.handleOverlayPreviousClick.bind(this))
    this.$.overlayNext.addEventListener("click", this.handleOverlayNextClick.bind(this))
  }

  registerSubscriptions() {
    appStore.subscribeState(this.onStateChanged.bind(this))
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.imageUrl = typeof state.imageUrl === "string" ? state.imageUrl : ""
    this._state.imageOriginalUrl = typeof state.imageOriginalUrl === "string" ? state.imageOriginalUrl : ""
    this._state.imageBackups = Array.isArray(state.imageBackups) ? state.imageBackups : []
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
    const imageOriginalUrlChanged = prevState.imageOriginalUrl !== state.imageOriginalUrl
    const imageBackupsChanged = prevState.imageBackups !== state.imageBackups
    const videoSourceChanged = prevState.videoUrl !== state.videoUrl || prevState.imageIsOriginal !== state.imageIsOriginal
    const autoplayRequested = prevState.imageVideoAutoplayRequestedAt !== state.imageVideoAutoplayRequestedAt
    const shouldRender = this.hasRenderChange(changedKeys)

    this.syncFromStore()

    this.resetOverlayImageIndexIfNeeded(imageUrlChanged, imageOriginalUrlChanged, imageBackupsChanged)

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
    return changedKeys.some((key) => [
      "imageUrl",
      "imageOriginalUrl",
      "imageBackups",
      "imageSignature",
      "isImageExpanded",
      "isImageRefreshLoading",
      "videoUrl",
      "imageIsOriginal",
    ].includes(key))
  }

  resetOverlayImageIndexIfNeeded(imageUrlChanged, imageOriginalUrlChanged, imageBackupsChanged) {
    if (imageUrlChanged || imageOriginalUrlChanged || imageBackupsChanged) {
      this._state.overlayImageIndex = 0
    }
  }

  syncVideoSources() {
    this.syncVideoSource(this.$.inlineVideo, this.hasActiveVideo())
    this.syncVideoSource(this.$.overlayVideo, Boolean(this._state.videoUrl))
  }

  syncVideoSource(video, hasVideo) {
    video.muted = true
    video.defaultMuted = true
    if (hasVideo) {
      if (video.getAttribute("src") !== this._state.videoUrl) {
        video.src = this._state.videoUrl
        video.load()
      }
    } else {
      video.removeAttribute("src")
      video.load()
    }
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
    this.openOrPlayInlineVideo()
  }

  handleContentClick(event) {
    event.stopPropagation()
    this.openOrPlayInlineVideo()
  }

  openOrPlayInlineVideo() {
    if (this.requestExpandFromUserGesture()) {
      return
    }
    this.playInlineVideoFromUserGesture()
  }

  handleMainKeyDown(event) {
    if (event.key !== "Enter" && event.key !== " ") {
      return
    }

    event.preventDefault()
    if (this.requestExpandFromUserGesture()) {
      return
    }
    this.playInlineVideoFromUserGesture()
  }

  handleInlineVideoClick(event) {
    event.stopPropagation()
    this.openOrPlayInlineVideo()
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
    if (this._suppressNextOverlayClick) {
      this._suppressNextOverlayClick = false
      return
    }

    if (!this._state.isExpanded) {
      return
    }

    this.requestCollapseFromUserGesture()
  }

  handleOverlayKeyDown(event) {
    if (event.key === "Escape") {
      event.preventDefault()
      this.requestCollapseFromUserGesture()
    }

    if (event.key === "ArrowLeft") {
      event.preventDefault()
      this.showPreviousOverlayImage()
    }

    if (event.key === "ArrowRight") {
      event.preventDefault()
      this.showNextOverlayImage()
    }
  }

  handleOverlayPreviousClick(event) {
    event.stopPropagation()
    this.showPreviousOverlayImage()
  }

  handleOverlayNextClick(event) {
    event.stopPropagation()
    this.showNextOverlayImage()
  }

  handleOverlayPointerDown(event) {
    if (event.target.closest("button")) {
      return
    }

    this._overlaySwipeStart = { x: event.clientX, y: event.clientY, pointerId: event.pointerId }
    try {
      this.$.overlayFrame.setPointerCapture(event.pointerId)
    } catch {
      // Synthetic pointer events may not provide an active capture target.
    }
  }

  handleOverlayPointerUp(event) {
    if (!this._overlaySwipeStart || this._overlaySwipeStart.pointerId !== event.pointerId) {
      return
    }

    const dx = event.clientX - this._overlaySwipeStart.x
    const dy = event.clientY - this._overlaySwipeStart.y
    this._overlaySwipeStart = null

    if (Math.abs(dx) < 48 || Math.abs(dx) < Math.abs(dy) * 1.2) {
      return
    }

    event.preventDefault()
    event.stopPropagation()
    this._suppressNextOverlayClick = true
    if (dx < 0) {
      this.showNextOverlayImage()
    } else {
      this.showPreviousOverlayImage()
    }
  }

  handleOverlayPointerCancel() {
    this._overlaySwipeStart = null
  }

  showPreviousOverlayImage() {
    if (this._state.overlayImageIndex <= 0) return
    this._state.overlayImageIndex -= 1
    this._applyOverlayNavigation()
  }

  showNextOverlayImage() {
    const images = this.getOverlayImages()
    if (this._state.overlayImageIndex >= images.length - 1) return
    this._state.overlayImageIndex += 1
    this._applyOverlayNavigation()
  }

  _applyOverlayNavigation() {
    this.renderOverlayImage()
    this.renderOverlayVideo(this._state.isExpanded)
    this.renderOverlayNavigation()
  }

  requestExpandFromUserGesture() {
    if (!this.canOpenOverlay()) {
      return false
    }

    this._lastFocusedElement = document.activeElement
    this._state.overlayImageIndex = 0
    appActions.toggleImageExpand(true)
    return true
  }

  requestCollapseFromUserGesture() {
    appActions.toggleImageExpand(false)
    this.clearOverlayPreloads()
    this.restoreFocus()
  }

  canOpenOverlay() {
    return Boolean(this._state.imageUrl)
  }

  restoreFocus() {
    if (this._lastFocusedElement instanceof HTMLElement) {
      this._lastFocusedElement.focus()
    }
  }

  render() {
    const hasImage = typeof this._state.imageUrl === "string" && this._state.imageUrl.trim().length > 0
    const overlayIsOpen = Boolean(this._state.isExpanded && hasImage)
    this.renderFrameState(hasImage, overlayIsOpen)

    if (!hasImage) {
      return
    }

    this.renderOverlayImage()

    const currentSrc = this.$.main.getAttribute("src") || ""
    if (currentSrc === this._state.imageUrl) {
      return
    }

    const shouldAnimate = this.shouldAnimateImageUpdate()

    if (shouldAnimate) {
      this.playImageUpdateAnimationAfterLoad(this._state.imageUrl)
    }

    ;[this.$.bg, this.$.main].forEach((img) => {
      img.src = this._state.imageUrl
    })
  }

  renderFrameState(hasImage, overlayIsOpen) {
    const showLoadingState = Boolean(this._state.isLoading && hasImage)
    const isSceneThumbnail = this.classList.contains("sg-scene-thumbnail")

    this.$.frame.classList.toggle("sg-hidden", !hasImage)
    this.$.frame.classList.toggle("is-loading", showLoadingState && !isSceneThumbnail)
    this.$.overlay.classList.toggle("is-open", overlayIsOpen)

    if (overlayIsOpen) {
      this.$.overlay.focus()
    } else {
      this.clearOverlayPreloads()
    }

    this.renderInlineVideo(hasImage)
    this.renderOverlayVideo(overlayIsOpen)
    this.renderOverlayNavigation()
  }

  getOverlayImages() {
    const backupUrls = this._state.imageBackups.map((backup) => backup.url).filter(Boolean)
    const originalUrl = this.shouldAppendOriginalImage(backupUrls) ? this._state.imageOriginalUrl : ""
    return [this._state.imageUrl, ...backupUrls, originalUrl].filter(Boolean)
  }

  shouldAppendOriginalImage(backupUrls) {
    if (!this._state.imageOriginalUrl) {
      return false
    }
    return backupUrls.length > 0 || !this._state.imageIsOriginal
  }

  getOverlayImageUrl() {
    const images = this.getOverlayImages()
    const index = Math.min(this._state.overlayImageIndex, Math.max(0, images.length - 1))
    this._state.overlayImageIndex = index
    return images[index] || this._state.imageUrl
  }

  renderOverlayImage() {
    const imageUrl = this.getOverlayImageUrl()
    if (this.$.overlayBg.getAttribute("src") !== imageUrl) {
      this.$.overlayBg.src = imageUrl
    }
    if (this.$.overlayMain.getAttribute("src") !== imageUrl) {
      this.playOverlayImageTransition()
      this.$.overlayMain.src = imageUrl
    }
    this.preloadNextOverlayImages()
  }

  preloadNextOverlayImages() {
    if (!this._state.isExpanded) {
      return
    }

    const images = this.getOverlayImages()
    const preloadUrls = images.slice(this._state.overlayImageIndex + 1, this._state.overlayImageIndex + 3)
    this.keepOnlyOverlayPreloads(preloadUrls)

    for (const url of preloadUrls) {
      if (this._overlayPreloadedImages.has(url)) {
        continue
      }
      const image = new Image()
      image.decoding = "async"
      image.src = url
      this._overlayPreloadedImages.set(url, image)
    }
  }

  keepOnlyOverlayPreloads(preloadUrls) {
    const keep = new Set(preloadUrls)
    for (const url of this._overlayPreloadedImages.keys()) {
      if (!keep.has(url)) {
        this._overlayPreloadedImages.delete(url)
      }
    }
  }

  clearOverlayPreloads() {
    this._overlayPreloadedImages.clear()
  }

  playOverlayImageTransition() {
    const previousSrc = this.$.overlayMain.getAttribute("src") || ""
    if (previousSrc && previousSrc !== "data:,") {
      this.$.overlayPrevious.src = previousSrc
      this.$.overlayPrevious.classList.remove("is-fading")
      void this.$.overlayPrevious.offsetWidth
      this.$.overlayPrevious.classList.add("is-fading")
    }

    this.$.overlayMain.classList.remove("is-switching")
    void this.$.overlayMain.offsetWidth
    this.$.overlayMain.classList.add("is-switching")

    if (this._overlayTransitionTimer !== null) {
      window.clearTimeout(this._overlayTransitionTimer)
    }

    this._overlayTransitionTimer = window.setTimeout(() => {
      this.$.overlayMain.classList.remove("is-switching")
      this.$.overlayPrevious.classList.remove("is-fading")
      this._overlayTransitionTimer = null
    }, 300)
  }

  renderOverlayNavigation() {
    const images = this.getOverlayImages()
    const hasMultipleImages = images.length > 1
    this.$.overlayPreviousButton.classList.toggle("sg-hidden", !hasMultipleImages || this._state.overlayImageIndex <= 0)
    this.$.overlayNext.classList.toggle("sg-hidden", !hasMultipleImages || this._state.overlayImageIndex >= images.length - 1)
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
    const videoActive = Boolean(overlayIsOpen && this._state.videoUrl && this.isOverlayShowingOriginalImage())
    const video = this.$.overlayVideo

    this.$.overlayMain.classList.toggle("sg-hidden", videoActive)
    video.classList.toggle("is-visible", videoActive)

    if (videoActive) {
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

  isOverlayShowingOriginalImage() {
    if (this._state.imageIsOriginal && this._state.overlayImageIndex === 0) {
      return true
    }

    const backupUrls = this._state.imageBackups.map((backup) => backup.url).filter(Boolean)
    const originalIndex = this.shouldAppendOriginalImage(backupUrls) ? backupUrls.length + 1 : -1
    return this._state.overlayImageIndex === originalIndex
  }
}

customElements.get("sg-thumbnail") || customElements.define("sg-thumbnail", SocialGameThumbnail)
