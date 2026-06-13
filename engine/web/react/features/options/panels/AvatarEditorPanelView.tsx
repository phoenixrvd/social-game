import type { AvatarView } from "../../../state/appViewTypes"
import { DeleteIcon, RevertIcon, SaveIcon } from "../../../shared/icons"
import { SettingsAction } from "../../../shared/SettingsAction"
import { ReferenceImageInput } from "../../entities/ReferenceImageInput"

type AvatarEditorPanelViewProps = {
  avatar: AvatarView | null
  description: string
  referenceImageDataUrl: string | null
  previewImageDataUrl: string | null
  busy: boolean
  isPreviewing: boolean
  error: string
  onDescription: (value: string) => void
  onReferenceChange: (value: string | null) => void
  onPreviewChange: (value: string | null) => void
  onError: (value: string) => void
  onDescribe: () => void
  onPreview: () => void
  onSave: () => void
  onDelete: () => void
  onReset: () => void
}

export function AvatarEditorPanelView(props: AvatarEditorPanelViewProps) {
  const title = props.avatar ? `Avatar bearbeiten: ${props.avatar.name || props.avatar.id}` : "Avatar bearbeiten"
  return (
    <section className="sg-settings-section">
      <h3 className="sg-settings-heading">{title}</h3>
      <div className="sg-form-group">
        <label className="sg-form-label">
          Avatarbeschreibung <span className="sg-form-required">*</span>
        </label>
        <p className="sg-form-hint-small">Diese Beschreibung wird als Wissen über deinen Spielercharakter im Chat verwendet.</p>
        <textarea
          className="sg-settings-textarea chat-scrollbar"
          placeholder="Was soll der NPC über deinen Spielercharakter wissen?"
          aria-label="Avatarbeschreibung editieren"
          value={props.description}
          disabled={props.busy || !props.avatar}
          onChange={(event) => props.onDescription(event.currentTarget.value)}
        />
      </div>
      <ReferenceImageInput
        busy={props.busy || !props.avatar}
        isPreviewing={props.isPreviewing}
        canCreatePreview={Boolean(props.description.trim())}
        previewAlt="Vorschau des Avatar-Bilds"
        referenceImageDataUrl={props.referenceImageDataUrl}
        previewImageDataUrl={props.previewImageDataUrl}
        onReferenceChange={props.onReferenceChange}
        onPreviewChange={props.onPreviewChange}
        onDescribe={props.onDescribe}
        onPreview={props.onPreview}
        onError={props.onError}
        showClearAction
        allowUploadWithPreview
        clearPreviewOnly
        canDescribe={Boolean(props.previewImageDataUrl || props.referenceImageDataUrl)}
        extraActions={
          <SettingsAction
            compact
            icon={<RevertIcon />}
            title="Avatar zurücksetzen"
            danger
            disabled={props.busy || !props.avatar?.canResetAvatar}
            onClick={props.onReset}
          />
        }
      />
      {props.error ? <div className="sg-scene-error">{props.error}</div> : null}
      <div className="sg-settings-actions">
        <SettingsAction
          icon={<SaveIcon />}
          title="Speichern"
          description="Beschreibung und Bild sichern"
          disabled={props.busy || !props.avatar || !props.description.trim()}
          onClick={props.onSave}
        />
        <SettingsAction
          icon={<DeleteIcon />}
          title="Löschen"
          description="Eigenen Avatar entfernen"
          danger
          disabled={props.busy || !props.avatar?.isDynamicAvatar}
          onClick={props.onDelete}
        />
      </div>
    </section>
  )
}
