import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useImageDescribeAvatar, useImagePreviewAvatar } from "../../../api/generated/avatar/avatar"
import { useAppCommands } from "../../../state/appCommands"
import type { AppView } from "../../../state/appViewTypes"
import { imageUrlToDataUrl } from "../../../shared/blobUtils"
import { useConfirmDialog } from "../../../shared/ConfirmDialog"
import { errorText } from "../../../shared/imageUtils"
import { buildOptionsPath } from "../optionsRoutes"
import { AvatarEditorPanelView } from "./AvatarEditorPanelView"

export function AvatarEditorPanelContainer({ appView }: { appView: AppView }) {
  const navigate = useNavigate()
  const commands = useAppCommands()
  const confirm = useConfirmDialog()
  const describeAvatar = useImageDescribeAvatar()
  const previewAvatar = useImagePreviewAvatar()
  const [description, setDescription] = useState("")
  const [referenceImageDataUrl, setReferenceImageDataUrl] = useState<string | null>(null)
  const [previewImageDataUrl, setPreviewImageDataUrl] = useState<string | null>(null)
  const [localError, setLocalError] = useState("")
  const avatar = appView.avatar.active
  const busy = commands.pending.entity || describeAvatar.isPending || previewAvatar.isPending
  const error = localError || errorText(commands.errors.entity || describeAvatar.error || previewAvatar.error, "")

  useEffect(() => {
    setDescription(avatar?.description || "")
    setPreviewImageDataUrl(null)
    setLocalError("")
    void imageUrlToDataUrl(avatar?.imageUrl || "")
      .then(setReferenceImageDataUrl)
      .catch((err) => setLocalError(errorText(err, "Avatar-Bild konnte nicht geladen werden.")))
  }, [avatar?.description, avatar?.id, avatar?.imageUrl])

  function backToGeneral() {
    navigate(buildOptionsPath(appView.session.npcId, appView.session.sceneId, "general"))
  }

  async function describeImage() {
    setLocalError("")
    try {
      const response = await describeAvatar.mutateAsync({ data: { imageDataUrl: previewImageDataUrl || referenceImageDataUrl || "" } })
      setDescription(response.status === 200 ? response.data.description : "")
    } catch (err) {
      setLocalError(errorText(err, "Beschreibung aus Bild konnte nicht erstellt werden."))
    }
  }

  async function previewImage() {
    setLocalError("")
    try {
      const response = await previewAvatar.mutateAsync({
        data: { description: description.trim(), referenceImageDataUrl },
      })
      setPreviewImageDataUrl(response.status === 200 ? response.data.imageDataUrl : "")
    } catch (err) {
      setLocalError(errorText(err, "Bild aus Beschreibung konnte nicht erstellt werden."))
    }
  }

  async function saveAvatar() {
    if (!avatar) return
    const text = description.trim()
    if (!text) {
      setLocalError("Avatarbeschreibung ist erforderlich.")
      return
    }
    setLocalError("")
    await commands.updateAvatar(avatar.id, { description: text, imageDataUrl: previewImageDataUrl || referenceImageDataUrl })
    backToGeneral()
  }

  async function deleteAvatar() {
    if (!avatar?.isDynamicAvatar) return
    const accepted = await confirm({
      title: "Avatar löschen",
      message: `Soll der Avatar ${avatar.name || avatar.id} vollständig gelöscht werden?`,
      listItems: ["Beschreibung", "Avatar-Bild", "Avatar-Auswahl"],
      confirmLabel: "Löschen",
      danger: true,
    })
    if (!accepted) return
    await commands.deleteAvatar(avatar.id)
    backToGeneral()
  }

  async function resetAvatar() {
    if (!avatar) return
    const accepted = await confirm({
      title: "Avatar zurücksetzen",
      message: "Soll der aktive Avatar auf den initialen Stand zurückgesetzt werden?",
      listItems: ["lokale Beschreibung", "lokales Avatar-Bild"],
      confirmLabel: "Zurücksetzen",
      danger: true,
    })
    if (!accepted) return
    await commands.resetAvatar(avatar.id)
  }

  return (
    <AvatarEditorPanelView
      avatar={avatar}
      description={description}
      referenceImageDataUrl={referenceImageDataUrl}
      previewImageDataUrl={previewImageDataUrl}
      busy={busy}
      isPreviewing={previewAvatar.isPending}
      error={error}
      onDescription={setDescription}
      onReferenceChange={setReferenceImageDataUrl}
      onPreviewChange={setPreviewImageDataUrl}
      onError={setLocalError}
      onDescribe={describeImage}
      onPreview={previewImage}
      onSave={saveAvatar}
      onDelete={deleteAvatar}
      onReset={resetAvatar}
    />
  )
}
