import { useAppCommands } from "../../../state/appCommands"
import type { AppView } from "../../../state/appViewTypes"
import { useConfirmDialog } from "../../../shared/ConfirmDialog"
import { ImagePanelView } from "./ImagePanelView"

export function ImagePanelContainer({ appView, close }: { appView: AppView; close: () => void }) {
  const commands = useAppCommands()
  const confirm = useConfirmDialog()

  async function runConfirmed(action: "revert" | "delete") {
    const accepted = await confirm({
      title: action === "delete" ? "Bild löschen" : "Bild wiederherstellen",
      message:
        action === "delete"
          ? "Soll das aktuelle Bild wirklich gelöscht werden?"
          : "Soll das aktive Bild wirklich auf das letzte Backup zurückgesetzt werden?",
      confirmLabel: action === "delete" ? "Löschen" : "Wiederherstellen",
      danger: action === "delete",
    })
    if (!accepted) return
    if (action === "delete") await commands.deleteImage()
    if (action === "revert") await commands.revertImage()
    close()
  }

  return (
    <ImagePanelView
      appView={appView}
      commands={commands}
      onRefresh={() => {
        close()
        void commands.refreshImage()
      }}
      onRevert={() => runConfirmed("revert")}
      onDelete={() => runConfirmed("delete")}
    />
  )
}
