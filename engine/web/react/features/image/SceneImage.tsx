import { useEffect, useRef, useState } from "react"
import { useIsMutating } from "@tanstack/react-query"
import type { AppStateView } from "../../api/types"
import { EMPTY_IMAGE, overlayImages } from "../../shared/imageUtils"
import { ImageOverlay } from "./ImageOverlay"

type SceneImageProps = {
  className?: string
  imageState?: AppStateView
}

export function SceneImage({ className = "", imageState }: SceneImageProps) {
  const [open, setOpen] = useState(false)
  const [index, setIndex] = useState(0)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const previousVideoKeyRef = useRef<string | null>(null)
  const images = overlayImages(imageState)
  const imageUrl = imageState?.imageUrl || null
  const videoUrl = imageState?.videoUrl || null
  const hasImage = Boolean(imageUrl)
  const showVideo = Boolean(videoUrl && imageState?.imageIsOriginal !== false)
  const isRefreshing = useIsMutating({ mutationKey: ["image"] }) > 0

  useEffect(() => setIndex(0), [imageUrl, imageState?.imageSignature])

  useEffect(() => {
    const video = videoRef.current
    const videoKey = `${imageState?.imageSignature || ""}::${videoUrl || ""}::${showVideo ? "1" : "0"}`
    if (!showVideo || !video) {
      previousVideoKeyRef.current = videoKey
      return
    }
    if (!previousVideoKeyRef.current) {
      previousVideoKeyRef.current = videoKey
      return
    }
    if (previousVideoKeyRef.current === videoKey) return
    previousVideoKeyRef.current = videoKey
    video.currentTime = 0
    void video.play().catch(() => {})
  }, [imageState?.imageSignature, showVideo, videoUrl])

  return (
    <div className={className}>
      <div className={`sg-image-frame ${hasImage ? "" : "sg-hidden"}${isRefreshing ? " is-loading" : ""}`}>
        <button type="button" className="sg-image-content sg-image-button" aria-label="Bild vergrößern" disabled={!hasImage} onClick={() => setOpen(true)}>
          <img className="sg-image-bg" src={imageUrl || EMPTY_IMAGE} alt="" aria-hidden="true" loading="lazy" decoding="async" />
          <img className="sg-image-main" src={imageUrl || EMPTY_IMAGE} alt="Szenenbild" loading="lazy" decoding="async" />
          {videoUrl ? <video ref={videoRef} className={`sg-image-inline-video ${showVideo ? "is-visible" : ""}`} src={videoUrl} preload="auto" muted playsInline autoPlay={showVideo} disablePictureInPicture /> : null}
        </button>
      </div>
      <ImageOverlay
        open={open && hasImage}
        images={images}
        index={index}
        setIndex={setIndex}
        videoUrl={videoUrl}
        imageIsOriginal={imageState?.imageIsOriginal ?? true}
        onClose={() => setOpen(false)}
      />
    </div>
  )
}
