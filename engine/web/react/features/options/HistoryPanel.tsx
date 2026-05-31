import { useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import {
  getSessionHistoryCheckpointsQueryKey,
  useSessionHistoryCheckpoints,
  useSessionHistoryCreateCheckpoint,
  useSessionHistoryRestoreCheckpoint,
} from "../../api/generated/session/session"
import type { CheckpointResponse as Checkpoint } from "../../api/generated/model"
import { stateQueryKey } from "../../api/state"
import { useConfirmDialog } from "../../shared/ConfirmDialog"
import { RestoreIcon, SaveIcon } from "../../shared/icons"
import { SettingsAction } from "../../shared/SettingsAction"
import { errorText } from "../../shared/imageUtils"

export function HistoryPanel() {
  const queryClient = useQueryClient()
  const confirm = useConfirmDialog()
  const checkpointsQueryKey = getSessionHistoryCheckpointsQueryKey()
  const checkpoints = useSessionHistoryCheckpoints({ query: { enabled: true } })
  const saveCheckpoint = useSessionHistoryCreateCheckpoint({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: checkpointsQueryKey })
      },
    },
  })
  const restoreCheckpoint = useSessionHistoryRestoreCheckpoint({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: stateQueryKey })
        void queryClient.invalidateQueries({ queryKey: checkpointsQueryKey })
      },
    },
  })
  const [actionError, setActionError] = useState("")
  const rawCheckpoints = checkpoints.data?.data
  const items = rawCheckpoints && typeof rawCheckpoints === "object" && "checkpoints" in rawCheckpoints && Array.isArray(rawCheckpoints.checkpoints)
    ? (rawCheckpoints.checkpoints as Checkpoint[])
    : []
  const error = actionError || errorText(checkpoints.error, "")
  const busy = saveCheckpoint.isPending || restoreCheckpoint.isPending

  async function save() {
    setActionError("")
    try {
      await saveCheckpoint.mutateAsync()
    } catch (err) {
      setActionError(errorText(err, "Checkpoint konnte nicht erstellt werden."))
    }
  }

  async function restore(commitHash: string) {
    const accepted = await confirm({ title: "Spielstand wiederherstellen", message: "Soll dieser Spielstand wirklich wiederhergestellt werden?", confirmLabel: "Wiederherstellen" })
    if (!accepted) return
    setActionError("")
    try {
      await restoreCheckpoint.mutateAsync({ commitHash })
    } catch (err) {
      setActionError(errorText(err, "Spielstand konnte nicht wiederhergestellt werden."))
    }
  }

  return (
    <section className="sg-settings-section">
      <h3 className="sg-settings-heading">Zwischenstände</h3>
      <div className="sg-checkpoint-list-container">
        <div className="sg-checkpoint-list" role="region" aria-label="Gespeicherte Spielstände">
          {items.map((checkpoint) => <CheckpointItem key={checkpoint.commitHash} checkpoint={checkpoint} onRestore={restore} />)}
        </div>
        {!items.length && !error ? <div className="sg-checkpoint-empty">Keine Spielstände vorhanden</div> : null}
      </div>
      {error ? <div className="sg-checkpoint-error">{error}</div> : null}
      <SettingsAction icon={<SaveIcon />} title="Zwischenstand speichern" description="Speichert den aktuellen Stand als wiederherstellbaren Checkpoint" disabled={busy} onClick={save} />
    </section>
  )
}

function CheckpointItem({ checkpoint, onRestore }: { checkpoint: Checkpoint; onRestore: (commitHash: string) => void }) {
  const autoBackup = checkpoint.commitMessage.includes("[auto-backup]")
  const label = autoBackup ? checkpoint.commitMessage.replace("[auto-backup]", "").trim() : checkpoint.commitMessage

  return (
    <button type="button" className={`sg-checkpoint-item${autoBackup ? " sg-checkpoint-item--auto-backup" : ""}`} aria-label={`Checkpoint: ${label}`} onClick={() => onRestore(checkpoint.commitHash)}>
      <span className="sg-checkpoint-item-icon" aria-hidden="true"><RestoreIcon /></span>
      <span className="sg-checkpoint-item-body">
        <span className="sg-checkpoint-title">{label}</span>
        <span className="sg-checkpoint-date">{checkpoint.commitDate}{autoBackup ? " · Auto-Backup" : ""}</span>
      </span>
    </button>
  )
}
