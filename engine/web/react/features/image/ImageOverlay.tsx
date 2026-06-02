import { useEffect, useRef } from "react"
import { EMPTY_IMAGE } from "../../shared/imageUtils"
import { useBodyScrollLock } from "../../shared/hooks/useBodyScrollLock"

type ImageOverlayProps = {
  open: boolean
  images: string[]
  index?: number
  setIndex?: (index: number) => void
  videoUrl?: string | null
  imageIsOriginal?: boolean
  onClose: () => void
}

export function ImageOverlay({
  open,
  images,
  index = 0,
  setIndex,
  videoUrl,
  imageIsOriginal = true,
  onClose,
}: ImageOverlayProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const lastImageIndex = Math.max(0, images.length - 1)
  const selectedImageIndex = clampIndex(index, lastImageIndex)
  const imageUrl = images[selectedImageIndex] || EMPTY_IMAGE
  const showVideo = Boolean(open && videoUrl && imageIsOriginal && index === 0)
  const hasPreviousImage = images.length > 1 && index > 0
  const hasNextImage = images.length > 1 && index < lastImageIndex
  useBodyScrollLock(open)

  function showPreviousImage() {
    setIndex?.(clampIndex(index - 1, lastImageIndex))
  }

  function showNextImage() {
    setIndex?.(clampIndex(index + 1, lastImageIndex))
  }

  useEffect(() => {
    if (!open) return
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose()
      if (event.key === "ArrowLeft") showPreviousImage()
      if (event.key === "ArrowRight") showNextImage()
    }
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [open, index, images.length, onClose, setIndex, lastImageIndex])

  useEffect(() => {
    if (!showVideo || !videoRef.current) return
    videoRef.current.currentTime = 0
    void videoRef.current.play()
  }, [showVideo, videoUrl])

  return (
    <div
      className={`sg-image-overlay ${open ? "is-open" : ""}`}
      role="dialog"
      aria-modal="true"
      aria-label="Vergrößertes Szenenbild"
      tabIndex={-1}
      onClick={onClose}
    >
      <div className="sg-image-overlay-frame">
        <img className="sg-image-overlay-bg" src={imageUrl} alt="" aria-hidden="true" loading="lazy" decoding="async" />
        <img
          className={`sg-image-overlay-main ${showVideo ? "sg-hidden" : ""}`}
          src={imageUrl}
          alt="Szenenbild"
          loading="lazy"
          decoding="async"
        />
        {videoUrl ? (
          <video
            ref={videoRef}
            className={`sg-image-overlay-video ${showVideo ? "is-visible" : ""}`}
            src={videoUrl}
            preload="auto"
            muted
            playsInline
            autoPlay={showVideo}
            disablePictureInPicture
          />
        ) : null}
        {hasPreviousImage ? (
          <button
            className="sg-image-overlay-nav sg-image-overlay-nav-left"
            type="button"
            aria-label="Vorheriges Bild anzeigen"
            onClick={(event) => {
              event.stopPropagation()
              showPreviousImage()
            }}
          >
            ‹
          </button>
        ) : null}
        {hasNextImage ? (
          <button
            className="sg-image-overlay-nav sg-image-overlay-nav-right"
            type="button"
            aria-label="Älteres Bild anzeigen"
            onClick={(event) => {
              event.stopPropagation()
              showNextImage()
            }}
          >
            ›
          </button>
        ) : null}
      </div>
    </div>
  )
}

function clampIndex(index: number, lastIndex: number) {
  return Math.min(Math.max(index, 0), lastIndex)
}
