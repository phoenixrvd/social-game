import type { CheckpointResponse as Checkpoint } from "../../../api/generated/model"
import { RestoreIcon, SaveIcon } from "../../../shared/icons"
import { SettingsAction } from "../../../shared/SettingsAction"

type HistoryPanelViewProps = {
  items: Checkpoint[]
  error: string
  busy: boolean
  onSave: () => void
  onRestore: (hash: string) => void
}

export function HistoryPanelView({ items, error, busy, onSave, onRestore }: HistoryPanelViewProps) {
  return (
    <section className="sg-settings-section">
      <h3 className="sg-settings-heading">Zwischenstände</h3>
      <div className="sg-checkpoint-list-container">
        <div className="sg-checkpoint-list" role="region" aria-label="Gespeicherte Spielstände">
          {items.map((checkpoint) => (
            <CheckpointItem key={checkpoint.commitHash} checkpoint={checkpoint} onRestore={onRestore} />
          ))}
        </div>
        {!items.length && !error ? <div className="sg-checkpoint-empty">Keine Spielstände vorhanden</div> : null}
      </div>
      {error ? <div className="sg-checkpoint-error">{error}</div> : null}
      <SettingsAction
        icon={<SaveIcon />}
        title="Zwischenstand speichern"
        description="Speichert den aktuellen Stand als wiederherstellbaren Checkpoint"
        disabled={busy}
        onClick={onSave}
      />
    </section>
  )
}

function CheckpointItem({
  checkpoint,
  onRestore,
}: {
  checkpoint: Checkpoint
  onRestore: (commitHash: string) => void
}) {
  const autoBackup = checkpoint.commitMessage.includes("[auto-backup]")
  const label = autoBackup ? checkpoint.commitMessage.replace("[auto-backup]", "").trim() : checkpoint.commitMessage
  return (
    <button
      type="button"
      className={`sg-checkpoint-item${autoBackup ? " sg-checkpoint-item--auto-backup" : ""}`}
      aria-label={`Checkpoint: ${label}`}
      onClick={() => onRestore(checkpoint.commitHash)}
    >
      <span className="sg-checkpoint-item-icon" aria-hidden="true">
        <RestoreIcon />
      </span>
      <span className="sg-checkpoint-item-body">
        <span className="sg-checkpoint-title">{label}</span>
        <span className="sg-checkpoint-date">
          {checkpoint.commitDate}
          {autoBackup ? " · Auto-Backup" : ""}
        </span>
      </span>
    </button>
  )
}
