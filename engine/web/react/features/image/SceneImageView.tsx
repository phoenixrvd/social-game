import { useEffect, useRef } from "react"
import { EMPTY_IMAGE } from "../../shared/imageUtils"
import { ImageOverlay } from "./ImageOverlay"

type SceneImageViewProps = {
  className: string
  imageUrl: string | null
  videoUrl: string | null
  imageIsOriginal: boolean
  images: string[]
  isRefreshing: boolean
  open: boolean
  index: number
  setIndex: (index: number) => void
  onOpen: () => void
  onClose: () => void
}

export function SceneImageView(props: SceneImageViewProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const previousVideoKeyRef = useRef<string | null>(null)
  const hasImage = Boolean(props.imageUrl)
  const showVideo = Boolean(props.videoUrl && props.imageIsOriginal !== false)
  const imageSource = props.imageUrl || EMPTY_IMAGE
  const imageFrameClassName = `sg-image-frame ${hasImage ? "" : "sg-hidden"}${props.isRefreshing ? " is-loading" : ""}`

  useEffect(() => {
    const video = videoRef.current
    const videoKey = videoPlaybackKey(props.imageUrl, props.videoUrl, showVideo)
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
  }, [props.imageUrl, props.videoUrl, showVideo])

  return (
    <div className={props.className}>
      <div className={imageFrameClassName}>
        <button
          type="button"
          className="sg-image-content sg-image-button"
          aria-label="Bild vergrößern"
          disabled={!hasImage}
          onClick={props.onOpen}
        >
          <img className="sg-image-bg" src={imageSource} alt="" aria-hidden="true" loading="lazy" decoding="async" />
          <img className="sg-image-main" src={imageSource} alt="Szenenbild" loading="lazy" decoding="async" />
          {props.videoUrl ? (
            <video
              ref={videoRef}
              className={`sg-image-inline-video ${showVideo ? "is-visible" : ""}`}
              src={props.videoUrl}
              preload="auto"
              muted
              playsInline
              autoPlay={showVideo}
              disablePictureInPicture
            />
          ) : null}
        </button>
      </div>
      <ImageOverlay
        open={props.open && hasImage}
        images={props.images}
        index={props.index}
        setIndex={props.setIndex}
        videoUrl={props.videoUrl}
        imageIsOriginal={props.imageIsOriginal}
        onClose={props.onClose}
      />
    </div>
  )
}

function videoPlaybackKey(imageUrl: string | null, videoUrl: string | null, showVideo: boolean) {
  const playbackState = showVideo ? "visible" : "hidden"
  return `${imageUrl || ""}::${videoUrl || ""}::${playbackState}`
}
