import type { AppCommands } from "../../../state/appCommands"
import type { AppView } from "../../../state/appViewTypes"
import { Checkbox } from "../../../shared/Checkbox"
import { DeleteIcon, SaveIcon, ThemeIcon } from "../../../shared/icons"
import { SettingsAction } from "../../../shared/SettingsAction"
import { errorText } from "../../../shared/imageUtils"

type GeneralPanelViewProps = {
  appView: AppView
  commands: AppCommands
  deleteNpc: boolean
  deleteScene: boolean
  deleteContext: boolean
  profile: string
  onProfile: (value: string) => void
  onSaveProfile: () => void
  onDeleteNpc: (value: boolean) => void
  onDeleteScene: (value: boolean) => void
  onDeleteContext: (value: boolean) => void
  onTheme: () => void
  onReset: () => void
}

export function GeneralPanelView(props: GeneralPanelViewProps) {
  const busy = props.commands.pending.profile || props.commands.pending.reset
  const error = errorText(props.commands.errors.profile || props.commands.errors.reset, "")
  return (
    <>
      <section className="sg-settings-section">
        <h3 className="sg-settings-heading">Allgemein</h3>
        <div className="sg-settings-actions">
          <SettingsAction
            icon={<ThemeIcon />}
            title="Theme wechseln"
            description="Zwischen hellem und dunklem Design wechseln"
            disabled={busy}
            onClick={props.onTheme}
          />
          <SettingsAction
            icon={<DeleteIcon />}
            title="Verlauf löschen"
            description="Entfernt Nachrichten und Bilder der aktiven Konversation"
            danger
            disabled={busy}
            onClick={props.onReset}
          />
          <Checkbox
            label="Erstellten NPC mit löschen"
            checked={props.deleteNpc}
            disabled={busy || !props.appView.npc.active?.isDynamicNpc}
            onChange={props.onDeleteNpc}
          />
          <Checkbox
            label="Erstellte Szene mit löschen"
            checked={props.deleteScene}
            disabled={busy || !props.appView.scene.active?.isDynamicScene}
            onChange={props.onDeleteScene}
          />
          <Checkbox
            label="Erstellten NPC-Kontext löschen"
            checked={props.deleteContext}
            disabled={busy || props.deleteNpc}
            onChange={props.onDeleteContext}
          />
        </div>
        {error ? <div className="sg-scene-error">{error}</div> : null}
      </section>
      <section className="sg-settings-section">
        <h3 className="sg-settings-heading">Nutzerprofil</h3>
        <div className="sg-form-group sg-user-profile-form">
          <label className="sg-form-label">User Profile</label>
          <p className="sg-form-hint-small">
            Beschreibe stabile Informationen, die der aktive NPC über die Nutzerin oder den Nutzer wissen soll.
          </p>
          <textarea
            className="sg-settings-textarea chat-scrollbar"
            aria-label="User Profile editieren"
            value={props.profile}
            disabled={busy}
            onChange={(event) => props.onProfile(event.currentTarget.value)}
          />
        </div>
        <div className="sg-settings-actions">
          <SettingsAction
            icon={<SaveIcon />}
            title="Profil speichern"
            description="Übernimmt das Profil für den aktiven Kontext"
            disabled={busy}
            onClick={props.onSaveProfile}
          />
        </div>
      </section>
    </>
  )
}
