import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useImageDescribeNpc, useImagePreviewNpc } from "../../api/generated/npc/npc"
import { useImageDescribeScene, useImagePreviewScene } from "../../api/generated/scene/scene"
import { useAppCommands } from "../../state/appCommands"
import type { AppView } from "../../state/appViewTypes"
import { useConfirmDialog } from "../../shared/ConfirmDialog"
import { imageUrlToDataUrl } from "../../shared/blobUtils"
import { errorText } from "../../shared/imageUtils"
import { buildOptionsPath } from "../options/optionsRoutes"
import { EntityEditorView } from "./EntityEditorView"

type EntityEditorProps =
  | { type: "scene"; mode: "create" | "edit"; appView: AppView; close?: () => void }
  | { type: "npc"; mode: "create"; appView: AppView; close?: () => void }

const CONFIG = {
  scene: {
    title: "Neue Szene für aktive Figur",
    editTitle: "Event Location bearbeiten",
    label: "Szenenbeschreibung",
    hint: "Die Beschreibung wird für die neue Szene und den NPC-Kontext verwendet.",
    placeholder: "z. B. Ein gemütliches Café mit warmem Licht, der NPC sitzt links am Fenster...",
    previewAlt: "Vorschau des Szenenbilds",
  },
  npc: {
    title: "Neue Figur erstellen",
    editTitle: "Neue Figur erstellen",
    label: "Charakterbeschreibung",
    hint: "Die Beschreibung wird verwendet, um Name, Charakter, initialen Zustand und Bild der neuen Figur zu erzeugen.",
    placeholder:
      "z. B. Alex ist ein ruhiger Koch Anfang 30, beobachtet genau und spricht selten direkt aus, was er denkt...",
    previewAlt: "Vorschau des NPC-Profilbilds",
  },
}

export function EntityEditorContainer({ type, mode, appView }: EntityEditorProps) {
  const navigate = useNavigate()
  const commands = useAppCommands()
  const confirm = useConfirmDialog()
  const describeScene = useImageDescribeScene()
  const describeNpc = useImageDescribeNpc()
  const previewScene = useImagePreviewScene()
  const previewNpc = useImagePreviewNpc()
  const imageMutations = [describeScene, describeNpc, previewScene, previewNpc]
  const [description, setDescription] = useState("")
  const [referenceImageDataUrl, setReferenceImageDataUrl] = useState<string | null>(null)
  const [previewImageDataUrl, setPreviewImageDataUrl] = useState<string | null>(null)
  const [localError, setLocalError] = useState("")
  const isScene = type === "scene"
  const isSceneEdit = type === "scene" && mode === "edit"
  const config = CONFIG[type]
  const busy = commands.pending.entity || imageMutations.some((mutation) => mutation.isPending)
  const isPreviewing = previewScene.isPending || previewNpc.isPending
  const imageMutationError = imageMutations.find((mutation) => mutation.error)?.error
  const mutationError = commands.errors.entity || imageMutationError
  const error = localError || errorText(mutationError, "")

  useEffect(() => {
    if (!isSceneEdit) return
    setDescription(appView.scene.active?.description || "")
    setLocalError("")
    void imageUrlToDataUrl(appView.scene.active?.imageUrl || "")
      .then((sceneImageDataUrl) => {
        setReferenceImageDataUrl(sceneImageDataUrl)
        setPreviewImageDataUrl(null)
      })
      .catch((err) => setLocalError(errorText(err, "Szenenbild konnte nicht geladen werden.")))
  }, [appView.scene.active?.description, appView.scene.active?.imageUrl, isSceneEdit])

  async function describeReference() {
    setLocalError("")
    try {
      const response = isScene
        ? await describeScene.mutateAsync({ data: { imageDataUrl: referenceImageDataUrl || "" } })
        : await describeNpc.mutateAsync({ data: { imageDataUrl: referenceImageDataUrl || "" } })
      setDescription(response.status === 200 ? response.data.description : "")
    } catch (err) {
      setLocalError(errorText(err, "Beschreibung aus Bild konnte nicht erstellt werden."))
    }
  }

  async function createPreview() {
    setLocalError("")
    try {
      const input = { description: description.trim(), referenceImageDataUrl }
      const response = isScene
        ? await previewScene.mutateAsync({ data: input })
        : await previewNpc.mutateAsync({ data: input })
      setPreviewImageDataUrl(response.status === 200 ? response.data.imageDataUrl : "")
    } catch (err) {
      setLocalError(errorText(err, "Bild aus Beschreibung konnte nicht erstellt werden."))
    }
  }

  async function submit() {
    const text = description.trim()
    if (!text) {
      setLocalError(isScene ? "Szenenbeschreibung ist erforderlich." : "Charakterbeschreibung ist erforderlich.")
      return
    }
    setLocalError("")
    if (isSceneEdit) {
      const imageDataUrl = previewImageDataUrl || referenceImageDataUrl || null
      await commands.updateScene(appView.session.sceneId, {
        description: text,
        imageDataUrl,
      })
      return
    }
    if (isScene) {
      const nextSceneId = await commands.createScene({
        description: text,
        imageDataUrl: previewImageDataUrl,
        referenceImageDataUrl,
      })
      if (nextSceneId) navigate(buildOptionsPath(appView.session.npcId, nextSceneId, "context"))
      return
    }
    const nextNpcId = await commands.createNpc({
      description: text,
      imageDataUrl: previewImageDataUrl,
      referenceImageDataUrl,
    })
    if (nextNpcId) navigate(buildOptionsPath(nextNpcId, appView.session.sceneId, "context"))
  }

  async function resetScene() {
    const accepted = await confirm({
      title: "Scene zurücksetzen",
      message: "Soll die aktive Scene auf den initialen Stand zurückgesetzt werden?",
      listItems: ["lokale Szenenänderungen", "NPC-Kontext", "Verlauf und Bilder dieser Scene"],
      confirmLabel: "Zurücksetzen",
      danger: true,
    })
    if (!accepted) return
    await commands.resetScene(appView.session.sceneId)
  }

  return (
    <EntityEditorView
      type={type}
      mode={mode}
      config={config}
      description={description}
      referenceImageDataUrl={referenceImageDataUrl}
      previewImageDataUrl={previewImageDataUrl}
      busy={busy}
      isPreviewing={isPreviewing}
      error={error}
      canResetScene={appView.scene.canReset}
      onDescription={setDescription}
      onReferenceChange={setReferenceImageDataUrl}
      onPreviewChange={setPreviewImageDataUrl}
      onError={setLocalError}
      onDescribe={describeReference}
      onPreview={createPreview}
      onSubmit={submit}
      onResetScene={resetScene}
    />
  )
}
