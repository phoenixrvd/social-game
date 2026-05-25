import { useEffect, useState } from "react"
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
  const images = overlayImages(imageState)
  const imageUrl = imageState?.imageUrl || null
  const hasImage = Boolean(imageUrl)

  useEffect(() => setIndex(0), [imageUrl, imageState?.imageSignature])

  return (
    <div className={className}>
      <div className={`sg-image-frame ${hasImage ? "" : "sg-hidden"}`}>
        <button type="button" className="sg-image-content sg-image-button" aria-label="Bild vergroessern" disabled={!hasImage} onClick={() => setOpen(true)}>
          <img className="sg-image-bg" src={imageUrl || EMPTY_IMAGE} alt="" aria-hidden="true" loading="lazy" decoding="async" />
          <img className="sg-image-main" src={imageUrl || EMPTY_IMAGE} alt="Szenenbild" loading="lazy" decoding="async" />
        </button>
      </div>
      <ImageOverlay
        open={open && hasImage}
        images={images}
        index={index}
        setIndex={setIndex}
        videoUrl={imageState?.videoUrl || null}
        imageIsOriginal={imageState?.imageIsOriginal ?? true}
        onClose={() => setOpen(false)}
      />
    </div>
  )
}
