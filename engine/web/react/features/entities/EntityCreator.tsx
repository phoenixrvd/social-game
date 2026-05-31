import {useEffect, useState} from "react"
import { useQueryClient } from "@tanstack/react-query"
import {
  getNpcListOptionsQueryKey,
  useImageDescribeNpc,
  useImagePreviewNpc,
  useNpcCreate,
} from "../../api/generated/npc/npc"
import {
  getSceneListOptionsQueryKey,
  useImageDescribeScene,
  useImagePreviewScene,
  useSceneResetActive,
  useSceneCreate,
  useSceneUpdate,
} from "../../api/generated/scene/scene"
import { stateQueryKey, useStateQuery } from "../../api/state"
import {useConfirmDialog} from "../../shared/ConfirmDialog"
import {PlusIcon, RevertIcon, SaveIcon} from "../../shared/icons"
import {SettingsAction} from "../../shared/SettingsAction"
import {errorText} from "../../shared/imageUtils"
import {useOptionsParams} from "../options/routes"
import {ReferenceImageInput} from "./ReferenceImageInput"

type EntityType = "scene" | "npc"
type EntityCreatorProps =
  | { type: "scene"; mode: "create" | "edit" }
  | { type: "npc"; mode: "create" }

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
    placeholder: "z. B. Alex ist ein ruhiger Koch Anfang 30, beobachtet genau und spricht selten direkt aus, was er denkt...",
    previewAlt: "Vorschau des NPC-Profilbilds",
  },
}

export function EntityCreator({ type, mode }: EntityCreatorProps) {
  const queryClient = useQueryClient()
  const { data } = useStateQuery()
  const confirm = useConfirmDialog()
  const options = useOptionsParams()

  async function syncAfterContextCreate(nextNpcId: string | null, nextSceneId: string | null) {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: getNpcListOptionsQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getSceneListOptionsQueryKey() }),
      queryClient.invalidateQueries({ queryKey: stateQueryKey }),
    ])
    if (nextNpcId && nextSceneId) {
      options.navigateToOptions(nextNpcId, nextSceneId, "context")
    }
  }

  const createScene = useSceneCreate({
    mutation: {
      onSuccess: async (response) => {
        const nextSceneId = typeof response.data === "object" && response.data && "id" in response.data && typeof response.data.id === "string"
          ? response.data.id
          : null
        await syncAfterContextCreate(data?.npcId ?? options.npcId ?? null, nextSceneId)
      },
    },
  })
  const updateActiveScene = useSceneUpdate({
    mutation: {
      onSuccess: (response) => {
        void queryClient.invalidateQueries({ queryKey: stateQueryKey })
      },
    },
  })
  const createNpc = useNpcCreate({
    mutation: {
      onSuccess: async (response) => {
        const nextNpcId = typeof response.data === "object" && response.data && "id" in response.data && typeof response.data.id === "string"
          ? response.data.id
          : null
        await syncAfterContextCreate(nextNpcId, data?.sceneId ?? options.sceneId ?? null)
      },
    },
  })
  const describeScene = useImageDescribeScene()
  const describeNpc = useImageDescribeNpc()
  const previewScene = useImagePreviewScene()
  const previewNpc = useImagePreviewNpc()
  const resetSceneMutation = useSceneResetActive({
    mutation: {
      onSuccess: (response) => {
        void queryClient.invalidateQueries({ queryKey: stateQueryKey })
      },
    },
  })
  const [description, setDescription] = useState("")
  const [referenceImageDataUrl, setReferenceImageDataUrl] = useState<string | null>(null)
  const [previewImageDataUrl, setPreviewImageDataUrl] = useState<string | null>(null)
  const [localError, setLocalError] = useState("")
  const isScene = type === "scene"
  const isSceneEdit = type === "scene" && mode === "edit"
  const config = CONFIG[type]
  const activeSceneImageUrl = isSceneEdit && data?.sceneId ? `/api/scenes/${data.sceneId}/image` : null
  const busy = createScene.isPending || updateActiveScene.isPending || createNpc.isPending || describeScene.isPending || describeNpc.isPending || previewScene.isPending || previewNpc.isPending || resetSceneMutation.isPending
  const mutationError = createScene.error || updateActiveScene.error || createNpc.error || describeScene.error || describeNpc.error || previewScene.error || previewNpc.error || resetSceneMutation.error
  const error = localError || errorText(mutationError, "")

  useEffect(() => {
    if (createScene.isSuccess || updateActiveScene.isSuccess || createNpc.isSuccess) {
      setDescription("")
      setReferenceImageDataUrl(null)
      setPreviewImageDataUrl(null)
      options.navigateToPanel("context")
    }
  }, [createNpc.isSuccess, createScene.isSuccess, options, updateActiveScene.isSuccess])

  useEffect(() => {
    if (!isSceneEdit || !data?.sceneId) return
    setDescription(data.sceneLocationDescription)
    setLocalError("")
    if (!activeSceneImageUrl) {
      setReferenceImageDataUrl(null)
      setPreviewImageDataUrl(null)
      return
    }
    void imageUrlToDataUrl(activeSceneImageUrl)
      .then((sceneImageDataUrl) => {
        setReferenceImageDataUrl(sceneImageDataUrl)
        setPreviewImageDataUrl(null)
      })
      .catch((error) => setLocalError(errorText(error, "Szenenbild konnte nicht geladen werden.")))
  }, [data?.sceneId, data?.sceneLocationDescription, activeSceneImageUrl, isSceneEdit])

  async function describeReference() {
    setLocalError("")
    try {
      if (isScene) {
        const response = await describeScene.mutateAsync({ data: { imageDataUrl: referenceImageDataUrl || "" } })
        setDescription(typeof response.data === "object" && response.data && "description" in response.data && typeof response.data.description === "string" ? response.data.description : "")
      } else {
        const response = await describeNpc.mutateAsync({ data: { imageDataUrl: referenceImageDataUrl || "" } })
        setDescription(typeof response.data === "object" && response.data && "description" in response.data && typeof response.data.description === "string" ? response.data.description : "")
      }
    } catch (error) {
      setLocalError(errorText(error, "Beschreibung aus Bild konnte nicht erstellt werden."))
    }
  }

  async function createPreview() {
    setLocalError("")
    try {
      const input = { description: description.trim(), referenceImageDataUrl }
      if (isScene) {
        const response = await previewScene.mutateAsync({ data: input })
        setPreviewImageDataUrl(typeof response.data === "object" && response.data && "imageDataUrl" in response.data && typeof response.data.imageDataUrl === "string" ? response.data.imageDataUrl : "")
      } else {
        const response = await previewNpc.mutateAsync({ data: input })
        setPreviewImageDataUrl(typeof response.data === "object" && response.data && "imageDataUrl" in response.data && typeof response.data.imageDataUrl === "string" ? response.data.imageDataUrl : "")
      }
    } catch (error) {
      setLocalError(errorText(error, "Bild aus Beschreibung konnte nicht erstellt werden."))
    }
  }

  function submit() {
    const text = description.trim()
    if (!text) {
      setLocalError(isScene ? "Szenenbeschreibung ist erforderlich." : "Charakterbeschreibung ist erforderlich.")
      return
    }
    setLocalError("")
    if (isSceneEdit) {
      if (!data?.sceneId) {
        setLocalError("Aktive Szene konnte nicht ermittelt werden.")
        return
      }
      updateActiveScene.mutate({ scene: data.sceneId, data: { description: text, imageDataUrl: previewImageDataUrl || referenceImageDataUrl || null } })
      return
    }
    if (isScene) {
      createScene.mutate({ data: { description: text, imageDataUrl: previewImageDataUrl, referenceImageDataUrl } })
      return
    }
    createNpc.mutate({ data: { description: text, imageDataUrl: previewImageDataUrl, referenceImageDataUrl } })
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
    if (!data?.sceneId) return
    await resetSceneMutation.mutateAsync({ scene: data.sceneId })
    options.close()
  }

  return (
    <section className="sg-settings-section">
      <h3 className="sg-settings-heading">{isSceneEdit ? config.editTitle : config.title}</h3>
      <div className="sg-form-group">
        <label className="sg-form-label">{config.label} <span className="sg-form-required">*</span></label>
        <p className="sg-form-hint-small">{config.hint}</p>
        <textarea className="sg-settings-textarea" value={description} placeholder={config.placeholder} required aria-required="true" disabled={busy} onChange={(event) => setDescription(event.currentTarget.value)} />
      </div>
      <ReferenceImageInput
        busy={busy}
        canCreatePreview={Boolean(description.trim())}
        previewAlt={config.previewAlt}
        referenceImageDataUrl={referenceImageDataUrl}
        previewImageDataUrl={previewImageDataUrl}
        onReferenceChange={setReferenceImageDataUrl}
        onPreviewChange={setPreviewImageDataUrl}
        onDescribe={describeReference}
        onPreview={createPreview}
        onError={setLocalError}
        extraActions={isSceneEdit ? <SettingsAction compact icon={<RevertIcon/>} title="Scene zurücksetzen" danger
                                                    disabled={busy || data?.canResetScene !== true}
                                                    onClick={resetScene}/> : null}
      />
      {error ? <div className="sg-scene-error">{error}</div> : null}
      <div className="sg-settings-actions">
        <SettingsAction icon={isSceneEdit ? <SaveIcon /> : <PlusIcon />} title={isSceneEdit ? "Scene speichern" : isScene ? "Szene erstellen" : "NPC erstellen"} description={isSceneEdit ? "Aktualisiert die aktive Event Location und den NPC-Kontext" : isScene ? "Erzeugt Szene und NPC-Kontext aus der Beschreibung" : "Erzeugt eine neue Figur aus deiner Charakterbeschreibung"} disabled={busy || !description.trim()} onClick={submit} />
      </div>
    </section>
  )
}

async function imageUrlToDataUrl(imageUrl: string): Promise<string> {
  const response = await fetch(imageUrl)
  if (!response.ok) throw new Error("Szenenbild konnte nicht geladen werden.")
  const blob = await response.blob()
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ""))
    reader.onerror = () => reject(new Error("Szenenbild konnte nicht gelesen werden."))
    reader.readAsDataURL(blob)
  })
}
