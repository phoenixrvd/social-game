import { PlusIcon, RevertIcon, SaveIcon } from "../../shared/icons"
import { SettingsAction } from "../../shared/SettingsAction"
import { ReferenceImageInput } from "./ReferenceImageInput"

export type EntityEditorConfig = {
  title: string
  editTitle: string
  label: string
  hint: string
  placeholder: string
  previewAlt: string
}

type EntityEditorViewProps = {
  type: "scene" | "npc"
  mode: "create" | "edit"
  config: EntityEditorConfig
  description: string
  referenceImageDataUrl: string | null
  previewImageDataUrl: string | null
  busy: boolean
  isPreviewing: boolean
  error: string
  canResetScene: boolean
  onDescription: (value: string) => void
  onReferenceChange: (value: string | null) => void
  onPreviewChange: (value: string | null) => void
  onError: (value: string) => void
  onDescribe: () => void
  onPreview: () => void
  onSubmit: () => void
  onResetScene: () => void
}

export function EntityEditorView(props: EntityEditorViewProps) {
  const isSceneEdit = props.type === "scene" && props.mode === "edit"
  return (
    <section className="sg-settings-section">
      <h3 className="sg-settings-heading">{isSceneEdit ? props.config.editTitle : props.config.title}</h3>
      <div className="sg-form-group">
        <label className="sg-form-label">
          {props.config.label} <span className="sg-form-required">*</span>
        </label>
        <p className="sg-form-hint-small">{props.config.hint}</p>
        <textarea
          className="sg-settings-textarea"
          value={props.description}
          placeholder={props.config.placeholder}
          required
          aria-required="true"
          disabled={props.busy}
          onChange={(event) => props.onDescription(event.currentTarget.value)}
        />
      </div>
      <ReferenceImageInput
        busy={props.busy}
        isPreviewing={props.isPreviewing}
        canCreatePreview={Boolean(props.description.trim())}
        previewAlt={props.config.previewAlt}
        referenceImageDataUrl={props.referenceImageDataUrl}
        previewImageDataUrl={props.previewImageDataUrl}
        onReferenceChange={props.onReferenceChange}
        onPreviewChange={props.onPreviewChange}
        onDescribe={props.onDescribe}
        onPreview={props.onPreview}
        onError={props.onError}
        extraActions={
          isSceneEdit ? (
            <SettingsAction
              compact
              icon={<RevertIcon />}
              title="Scene zurücksetzen"
              danger
              disabled={props.busy || props.canResetScene !== true}
              onClick={props.onResetScene}
            />
          ) : null
        }
      />
      {props.error ? <div className="sg-scene-error">{props.error}</div> : null}
      <div className="sg-settings-actions">
        <SettingsAction
          icon={isSceneEdit ? <SaveIcon /> : <PlusIcon />}
          title={submitTitle(props.type, isSceneEdit)}
          description={submitDescription(props.type, isSceneEdit)}
          disabled={props.busy || !props.description.trim()}
          onClick={props.onSubmit}
        />
      </div>
    </section>
  )
}

function submitTitle(type: "scene" | "npc", isSceneEdit: boolean) {
  if (isSceneEdit) return "Scene speichern"
  return type === "scene" ? "Szene erstellen" : "NPC erstellen"
}

function submitDescription(type: "scene" | "npc", isSceneEdit: boolean) {
  if (isSceneEdit) return "Aktualisiert die aktive Event Location und den NPC-Kontext"
  return type === "scene"
    ? "Erzeugt Szene und NPC-Kontext aus der Beschreibung"
    : "Erzeugt eine neue Figur aus deiner Charakterbeschreibung"
}
