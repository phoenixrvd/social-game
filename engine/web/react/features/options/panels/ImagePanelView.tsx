import type { AppCommands } from "../../../state/appCommands"
import type { AppView } from "../../../state/appViewTypes"
import { CheckedIcon, DeleteIcon, RefreshIcon, RevertIcon, UncheckedIcon } from "../../../shared/icons"
import { SettingsAction } from "../../../shared/SettingsAction"
import { errorText } from "../../../shared/imageUtils"

type ImagePanelViewProps = {
  appView: AppView
  commands: AppCommands
  onRefresh: () => void
  onRevert: () => void
  onDelete: () => void
}

export function ImagePanelView({ appView, commands, onRefresh, onRevert, onDelete }: ImagePanelViewProps) {
  const busy = commands.pending.session || commands.pending.image
  const error = errorText(commands.errors.image || commands.errors.session, "")
  return (
    <section className="sg-settings-section">
      <h3 className="sg-settings-heading">Bild</h3>
      <div className="sg-settings-actions">
        <SettingsAction
          icon={appView.image.autogenerate ? <CheckedIcon /> : <UncheckedIcon />}
          title="Automatische Bildgenerierung"
          description="Bilder werden automatisch neu generiert und mit dem Chatverlauf konsistent gehalten"
          ariaPressed={appView.image.autogenerate}
          inactive={!appView.image.autogenerate}
          disabled={busy}
          onClick={() =>
            commands.selectContext({
              npc: appView.session.npcId,
              scene: appView.session.sceneId,
              imageAutogenerate: !appView.image.autogenerate,
            })
          }
        />
        <SettingsAction
          icon={<RefreshIcon />}
          title="Neues Bild generieren"
          description="Erzeugt ein neues Bild aus dem aktuellen Chat-Kontext"
          disabled={busy}
          onClick={onRefresh}
        />
        <SettingsAction
          icon={<RevertIcon />}
          title="Vorheriges Bild wiederherstellen"
          description="Ersetzt das aktuelle Bild durch den vorherigen Bildstand"
          disabled={busy}
          onClick={onRevert}
        />
        <SettingsAction
          icon={<DeleteIcon />}
          title="Aktuelles Bild löschen"
          description="Entfernt das aktuelle Bild, ohne ein früheres Bild wiederherzustellen"
          danger
          disabled={busy}
          onClick={onDelete}
        />
      </div>
      {error ? <div className="sg-scene-error">{error}</div> : null}
    </section>
  )
}
