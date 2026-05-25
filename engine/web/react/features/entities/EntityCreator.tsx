import { useEffect, useState } from "react"
import {
  useCreateNpcMutation,
  useCreateSceneMutation,
  useDescribeNpcReferenceMutation,
  useDescribeSceneReferenceMutation,
  useNpcPreviewImageMutation,
  useScenePreviewImageMutation,
} from "../../api/entities"
import { PlusIcon } from "../../shared/icons"
import { SettingsAction } from "../../shared/SettingsAction"
import { errorText } from "../../shared/imageUtils"
import { useOptionsParams } from "../options/routes"
import { ReferenceImageInput } from "./ReferenceImageInput"

type EntityType = "scene" | "npc"

const CONFIG = {
  scene: {
    title: "Neue Szene für aktive Figur",
    label: "Szenenbeschreibung",
    hint: "Die Beschreibung wird für die neue Szene und den NPC-Kontext verwendet.",
    placeholder: "z. B. Ein gemütliches Café mit warmem Licht, der NPC sitzt links am Fenster...",
    previewAlt: "Vorschau des Szenenbilds",
  },
  npc: {
    title: "Neue Figur erstellen",
    label: "Charakterbeschreibung",
    hint: "Die Beschreibung wird verwendet, um Name, Charakter, initialen Zustand und Bild der neuen Figur zu erzeugen.",
    placeholder: "z. B. Alex ist ein ruhiger Koch Anfang 30, beobachtet genau und spricht selten direkt aus, was er denkt...",
    previewAlt: "Vorschau des NPC-Profilbilds",
  },
}

export function EntityCreator({ type }: { type: EntityType }) {
  const options = useOptionsParams()
  const createScene = useCreateSceneMutation()
  const createNpc = useCreateNpcMutation()
  const describeScene = useDescribeSceneReferenceMutation()
  const describeNpc = useDescribeNpcReferenceMutation()
  const previewScene = useScenePreviewImageMutation()
  const previewNpc = useNpcPreviewImageMutation()
  const [description, setDescription] = useState("")
  const [referenceImageDataUrl, setReferenceImageDataUrl] = useState<string | null>(null)
  const [previewImageDataUrl, setPreviewImageDataUrl] = useState<string | null>(null)
  const [localError, setLocalError] = useState("")
  const isScene = type === "scene"
  const config = CONFIG[type]
  const busy = createScene.isPending || createNpc.isPending || describeScene.isPending || describeNpc.isPending || previewScene.isPending || previewNpc.isPending
  const mutationError = createScene.error || createNpc.error || describeScene.error || describeNpc.error || previewScene.error || previewNpc.error
  const error = localError || errorText(mutationError, "")

  useEffect(() => {
    if (createScene.isSuccess || createNpc.isSuccess) {
      setDescription("")
      setReferenceImageDataUrl(null)
      setPreviewImageDataUrl(null)
      options.navigateToPanel("context")
    }
  }, [createNpc.isSuccess, createScene.isSuccess, options])

  async function describeReference() {
    setLocalError("")
    try {
      setDescription(isScene ? await describeScene.mutateAsync(referenceImageDataUrl) : await describeNpc.mutateAsync(referenceImageDataUrl))
    } catch (error) {
      setLocalError(errorText(error, "Beschreibung aus Bild konnte nicht erstellt werden."))
    }
  }

  async function createPreview() {
    setLocalError("")
    try {
      const input = { description: description.trim(), referenceImageDataUrl }
      setPreviewImageDataUrl(isScene ? await previewScene.mutateAsync(input) : await previewNpc.mutateAsync(input))
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
    if (isScene) {
      createScene.mutate({ sceneDescription: text, sceneImageDataUrl: previewImageDataUrl, referenceImageDataUrl })
      return
    }
    createNpc.mutate({ characterDescription: text, npcImageDataUrl: previewImageDataUrl, referenceImageDataUrl })
  }

  return (
    <section className="sg-settings-section">
      <h3 className="sg-settings-heading">{config.title}</h3>
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
      />
      {error ? <div className="sg-scene-error">{error}</div> : null}
      <SettingsAction icon={<PlusIcon />} title={isScene ? "Szene erstellen" : "NPC erstellen"} description={isScene ? "Erzeugt Szene und NPC-Kontext aus der Beschreibung" : "Erzeugt eine neue Figur aus deiner Charakterbeschreibung"} disabled={busy || !description.trim()} onClick={submit} />
    </section>
  )
}
