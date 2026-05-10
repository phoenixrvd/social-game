class SocialGameContextGalleryItem extends HTMLElement {
  connectedCallback() {
    if (!this.querySelector(".sg-context-gallery-media")) {
      this.innerHTML = /*html*/ `
        <span class="sg-context-gallery-media">
          <img class="sg-context-gallery-image" src="" alt="" loading="eager" />
        </span>
        <span class="sg-context-gallery-label"></span>
      `
    }

    this._initRefs()

    this.addEventListener("click", (e) => {
      const clickedMedia = Boolean(e.target.closest(".sg-context-gallery-media"))
      this.dispatchEvent(new CustomEvent("itemClicked", {
        bubbles: true,
        detail: { itemId: this.dataset.itemId, clickedMedia },
      }))
    })
  }

  _initRefs() {
    this.$ = {
      media: this.querySelector(".sg-context-gallery-media"),
      image: this.querySelector(".sg-context-gallery-image"),
      label: this.querySelector(".sg-context-gallery-label"),
    }
  }

  set selected(value) {
    this.classList.toggle("sg-context-gallery-item--selected", Boolean(value))
    this.setAttribute("aria-pressed", value ? "true" : "false")
  }

  update({ imageUrl, label, videoUrl }) {
    if (!this.$) this._initRefs()
    if (!this.$) return
    this.$.image.src = imageUrl
    this.$.image.alt = label
    this.$.label.textContent = label

    const hasVideo = typeof videoUrl === "string" && videoUrl.trim().length > 0
    let video = this.$.media.querySelector("video")

    if (hasVideo && !video) {
      video = document.createElement("video")
      video.className = "sg-context-gallery-video"
      video.preload = "auto"
      video.muted = true
      video.defaultMuted = true
      video.playsInline = true
      video.setAttribute("disablepictureinpicture", "")
      video.setAttribute("disableremoteplayback", "")
      video.src = videoUrl
      this.$.media.appendChild(video)
    } else if (!hasVideo && video) {
      video.remove()
    } else if (hasVideo && video && video.getAttribute("src") !== videoUrl) {
      video.src = videoUrl
    }
  }

  playVideo() {
    if (!this.$) this._initRefs()
    if (!this.$) return
    const video = this.$.media.querySelector("video")
    if (!video) return
    video.muted = true
    video.defaultMuted = true
    video.classList.add("sg-context-gallery-video--playing")
    video.currentTime = 0
    video.play().catch(() => {})
  }
}

customElements.get("sg-context-gallery-item") || customElements.define("sg-context-gallery-item", SocialGameContextGalleryItem)
