import { useQueryClient } from "@tanstack/react-query"
import {
  useImageCurrentDelete,
  useImageCurrentRefresh,
  useImageCurrentRevert,
  useSessionUpdateSession,
} from "../../api/generated/session/session"
import { imageSignatureQueryKey, stateQueryKey, useStateQuery } from "../../api/state"
import { useConfirmDialog } from "../../shared/ConfirmDialog"
import { CheckedIcon, DeleteIcon, RefreshIcon, RevertIcon, UncheckedIcon } from "../../shared/icons"
import { SettingsAction } from "../../shared/SettingsAction"
import { errorText } from "../../shared/imageUtils"
import { useOptionsParams } from "./routes"

export function ImagePanel() {
  const queryClient = useQueryClient()
  const { data } = useStateQuery()
  const confirm = useConfirmDialog()
  const options = useOptionsParams()
  const updateSession = useSessionUpdateSession({
    mutation: {
      onSuccess: (response) => {
        void queryClient.invalidateQueries({ queryKey: stateQueryKey })
      },
    },
  })
  const refreshImage = useImageCurrentRefresh({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: imageSignatureQueryKey })
        void queryClient.invalidateQueries({ queryKey: stateQueryKey })
      },
    },
  })
  const revertImage = useImageCurrentRevert({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: imageSignatureQueryKey })
        void queryClient.invalidateQueries({ queryKey: stateQueryKey })
      },
    },
  })
  const deleteImage = useImageCurrentDelete({
    mutation: {
      onSuccess: (response) => {
        void queryClient.invalidateQueries({ queryKey: stateQueryKey })
        void queryClient.invalidateQueries({ queryKey: imageSignatureQueryKey })
      },
    },
  })
  const busy = updateSession.isPending || refreshImage.isPending || revertImage.isPending || deleteImage.isPending
  const error = errorText(refreshImage.error || revertImage.error || deleteImage.error || updateSession.error, "")

  async function runConfirmed(action: "revert" | "delete") {
    const accepted = await confirm({
      title: action === "delete" ? "Bild löschen" : "Bild wiederherstellen",
      message: action === "delete" ? "Soll das aktuelle Bild wirklich gelöscht werden?" : "Soll das aktive Bild wirklich auf das letzte Backup zurückgesetzt werden?",
      confirmLabel: action === "delete" ? "Löschen" : "Wiederherstellen",
      danger: action === "delete",
    })
    if (!accepted) return
    if (action === "delete") await deleteImage.mutateAsync()
    if (action === "revert") await revertImage.mutateAsync()
    options.close()
  }

  return (
    <section className="sg-settings-section">
      <h3 className="sg-settings-heading">Bild</h3>
      <div className="sg-settings-actions">
        <SettingsAction icon={data?.imageAutogenerate ? <CheckedIcon /> : <UncheckedIcon />} title="Automatische Bildgenerierung" description="Bilder werden automatisch neu generiert und mit dem Chatverlauf konsistent gehalten" ariaPressed={Boolean(data?.imageAutogenerate)} inactive={!data?.imageAutogenerate} disabled={busy} onClick={() => updateSession.mutate({ data: { npc: data?.npcId || undefined, scene: data?.sceneId || undefined, imageAutogenerate: !data?.imageAutogenerate } })} />
        <SettingsAction icon={<RefreshIcon />} title="Neues Bild generieren" description="Erzeugt ein neues Bild aus dem aktuellen Chat-Kontext" disabled={busy} onClick={() => { options.close(); void refreshImage.mutateAsync() }} />
        <SettingsAction icon={<RevertIcon />} title="Vorheriges Bild wiederherstellen" description="Ersetzt das aktuelle Bild durch den vorherigen Bildstand" disabled={busy} onClick={() => runConfirmed("revert")} />
        <SettingsAction icon={<DeleteIcon />} title="Aktuelles Bild löschen" description="Entfernt das aktuelle Bild, ohne ein früheres Bild wiederherzustellen" danger disabled={busy} onClick={() => runConfirmed("delete")} />
      </div>
      {error ? <div className="sg-scene-error">{error}</div> : null}
    </section>
  )
}
