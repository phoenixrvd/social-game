import type { ChangeEvent } from "react"
import { useState } from "react"
import { DeleteIcon, ImageIcon, TextEditIcon } from "../../shared/icons"
import { SettingsAction } from "../../shared/SettingsAction"
import { resizeReferenceImage } from "../../shared/imageUtils"
import { ImageOverlay } from "../image/ImageOverlay"

type ReferenceImageInputProps = {
  busy: boolean
  canCreatePreview: boolean
  previewAlt: string
  referenceImageDataUrl: string | null
  previewImageDataUrl: string | null
  onReferenceChange: (imageDataUrl: string | null) => void
  onPreviewChange: (imageDataUrl: string | null) => void
  onDescribe: () => void
  onPreview: () => void
  onError: (message: string) => void
}

export function ReferenceImageInput({
  busy,
  canCreatePreview,
  previewAlt,
  referenceImageDataUrl,
  previewImageDataUrl,
  onReferenceChange,
  onPreviewChange,
  onDescribe,
  onPreview,
  onError,
}: ReferenceImageInputProps) {
  const [overlayOpen, setOverlayOpen] = useState(false)
  const visibleImageDataUrl = previewImageDataUrl || referenceImageDataUrl

  async function selectFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0]
    if (!file) return
    try {
      onReferenceChange(await resizeReferenceImage(file))
      onPreviewChange(null)
    } catch (error) {
      onError(error instanceof Error ? error.message : "Bild konnte nicht gelesen werden.")
    } finally {
      event.currentTarget.value = ""
    }
  }

  function clear() {
    onReferenceChange(null)
    onPreviewChange(null)
  }

  return (
    <div className="sg-scene-reference-panel">
      <label className="sg-scene-preview" data-empty={visibleImageDataUrl ? "false" : "true"} role="button" tabIndex={0} aria-label={previewImageDataUrl ? "Bildvorschau vergroessern" : "Referenzbild wählen"} onClick={(event) => { if (previewImageDataUrl) { event.preventDefault(); setOverlayOpen(true) } }}>
        <input className="sg-visually-hidden" type="file" accept="image/*" capture="environment" disabled={busy || Boolean(previewImageDataUrl)} onChange={selectFile} />
        <span className="sg-image-content">
          {visibleImageDataUrl ? (
            <>
              <img className="sg-image-bg" src={visibleImageDataUrl} alt="" aria-hidden="true" />
              <img className="sg-image-main" src={visibleImageDataUrl} alt={previewAlt} />
            </>
          ) : null}
        </span>
        {!visibleImageDataUrl ? <span className="sg-scene-preview-placeholder">Bild auswählen</span> : null}
      </label>
      <ImageOverlay open={overlayOpen} images={previewImageDataUrl ? [previewImageDataUrl] : []} onClose={() => setOverlayOpen(false)} />
      <div className="sg-scene-reference-actions">
        <SettingsAction compact icon={<TextEditIcon />} title="Beschreibung aus Bild" disabled={busy || !referenceImageDataUrl} onClick={onDescribe} />
        <SettingsAction compact icon={<ImageIcon />} title="Bild aus Beschreibung" disabled={busy || !canCreatePreview} onClick={onPreview} />
        <SettingsAction compact danger icon={<DeleteIcon />} title="Bild löschen" disabled={busy || !visibleImageDataUrl} onClick={clear} />
      </div>
    </div>
  )
}
