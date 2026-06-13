import { Link } from "react-router-dom"
import type { AppCommands } from "../../../state/appCommands"
import type { AppView, AvatarView } from "../../../state/appViewTypes"
import { Checkbox } from "../../../shared/Checkbox"
import { DeleteIcon, PencilIcon, PlusIcon, ThemeIcon } from "../../../shared/icons"
import { SettingsAction } from "../../../shared/SettingsAction"
import { errorText } from "../../../shared/imageUtils"
import { buildOptionsPath } from "../optionsRoutes"

type GeneralPanelViewProps = {
  appView: AppView
  commands: AppCommands
  deleteNpc: boolean
  deleteScene: boolean
  deleteContext: boolean
  onAvatarSelect: (avatar: string) => void
  onAvatarEdit: () => void
  onDeleteNpc: (value: boolean) => void
  onDeleteScene: (value: boolean) => void
  onDeleteContext: (value: boolean) => void
  onTheme: () => void
  onReset: () => void
}

export function GeneralPanelView(props: GeneralPanelViewProps) {
  const busy = props.commands.pending.profile || props.commands.pending.reset
  const error = errorText(props.commands.errors.profile || props.commands.errors.reset, "")
  const avatarBusy = busy || props.commands.pending.session || props.commands.pending.entity
  const activeAvatar = props.appView.avatar.active
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
        <h3 className="sg-selector-legend">Dein Avatar</h3>
        <AvatarGallery appView={props.appView} busy={avatarBusy} onSelect={props.onAvatarSelect} />
        <div className="sg-settings-actions">
          <SettingsAction
            icon={<PencilIcon />}
            title="Avatar bearbeiten"
            description="Beschreibung oder Bild ändern"
            disabled={avatarBusy || !activeAvatar}
            onClick={props.onAvatarEdit}
          />
        </div>
      </section>
    </>
  )
}

function AvatarGallery({ appView, busy, onSelect }: { appView: AppView; busy: boolean; onSelect: (avatar: string) => void }) {
  return (
    <div className="sg-context-gallery" data-context-type="avatar">
      <fieldset className="sg-context-gallery-fieldset">
        <div className="sg-context-gallery-scroll">
          {appView.avatar.options.map((avatar) => (
            <AvatarGalleryItem
              key={avatar.id}
              avatar={avatar}
              selected={avatar.id === appView.session.avatarId}
              disabled={busy}
              onSelect={onSelect}
            />
          ))}
          <Link
            className="sg-context-gallery-item sg-context-gallery-create sg-context-gallery-create-scene"
            aria-label="Avatar erstellen"
            to={buildOptionsPath(appView.session.npcId, appView.session.sceneId, "avatar-creator")}
          >
            <div className="sg-context-gallery-image sg-context-gallery-create-scene-image">
              <PlusIcon />
            </div>
            <span className="sg-context-gallery-label">Avatar erstellen</span>
          </Link>
        </div>
      </fieldset>
    </div>
  )
}

function AvatarGalleryItem({
  avatar,
  selected,
  disabled,
  onSelect,
}: {
  avatar: AvatarView
  selected: boolean
  disabled: boolean
  onSelect: (avatar: string) => void
}) {
  return (
    <button
      type="button"
      className={`sg-context-gallery-item ${selected ? "sg-context-gallery-item--selected" : ""}`}
      aria-current={selected ? "true" : undefined}
      disabled={disabled}
      onClick={() => {
        if (!selected) onSelect(avatar.id)
      }}
    >
      <span className="sg-context-gallery-media">
        <img className="sg-context-gallery-image" src={avatar.imageUrl} alt={avatar.name || avatar.id} loading="eager" />
      </span>
      <span className="sg-context-gallery-label">{avatar.name || avatar.id}</span>
    </button>
  )
}
