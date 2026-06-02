import type { AppCommands } from "../../../state/appCommands"
import { SaveIcon, TextEditIcon } from "../../../shared/icons"
import { SettingsAction } from "../../../shared/SettingsAction"
import { errorText } from "../../../shared/imageUtils"

type SceneContextPanelViewProps = {
  content: string
  commands: AppCommands
  onContent: (value: string) => void
  onGenerate: () => void
}

export function SceneContextPanelView({ content, commands, onContent, onGenerate }: SceneContextPanelViewProps) {
  const busy = commands.pending.sceneContext
  const error = errorText(commands.errors.sceneContext, "")
  return (
    <section className="sg-settings-section">
      <h3 className="sg-settings-heading">Scene Context bearbeiten</h3>
      <div className="sg-form-group">
        <label className="sg-form-label">
          Scene Context <span className="sg-form-required">*</span>
        </label>
        <p className="sg-form-hint-small">
          Beschreibe, wie der NPC in der Szene erscheint: z. B. wo er steht, wohin er schaut oder wie er angekleidet
          ist.
        </p>
        <textarea
          className="sg-settings-textarea"
          aria-label="Scene Context editieren"
          value={content}
          disabled={busy}
          onChange={(event) => onContent(event.currentTarget.value)}
        />
      </div>
      {error ? <div className="sg-scene-error">{error}</div> : null}
      <div className="sg-settings-actions">
        <SettingsAction
          icon={<TextEditIcon />}
          title="Neuen Kontext aus Eingabe generieren"
          description="Formt den Text zu einem neuen Kontext um"
          disabled={busy || !content.trim()}
          onClick={onGenerate}
        />
        <SettingsAction
          icon={<SaveIcon />}
          title="Kontext speichern"
          description="Übernimmt den Kontext für die aktive Szene"
          disabled={busy}
          onClick={() => commands.saveSceneContext(content)}
        />
      </div>
    </section>
  )
}
