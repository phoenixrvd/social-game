import { useState } from "react"
import { useSessionHistoryCheckpoints } from "../../../api/generated/session/session"
import { useAppCommands } from "../../../state/appCommands"
import { useConfirmDialog } from "../../../shared/ConfirmDialog"
import { errorText } from "../../../shared/imageUtils"
import { HistoryPanelView } from "./HistoryPanelView"

export function HistoryPanelContainer() {
  const commands = useAppCommands()
  const confirm = useConfirmDialog()
  const checkpoints = useSessionHistoryCheckpoints({ query: { enabled: true } })
  const [actionError, setActionError] = useState("")
  const items = checkpoints.data?.status === 200 ? checkpoints.data.data.checkpoints : []
  const error = actionError || errorText(checkpoints.error, "")

  async function save() {
    setActionError("")
    await commands
      .createCheckpoint()
      .catch((err) => setActionError(errorText(err, "Checkpoint konnte nicht erstellt werden.")))
  }

  async function restore(commitHash: string) {
    const accepted = await confirm({
      title: "Spielstand wiederherstellen",
      message: "Soll dieser Spielstand wirklich wiederhergestellt werden?",
      confirmLabel: "Wiederherstellen",
    })
    if (!accepted) return
    setActionError("")
    await commands
      .restoreCheckpoint(commitHash)
      .catch((err) => setActionError(errorText(err, "Spielstand konnte nicht wiederhergestellt werden.")))
  }

  return (
    <HistoryPanelView items={items} error={error} busy={commands.pending.history} onSave={save} onRestore={restore} />
  )
}
