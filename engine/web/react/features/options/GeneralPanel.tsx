import { useEffect, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { useNpcDelete, useNpcResetActive } from "../../api/generated/npc/npc"
import { getSceneListOptionsQueryKey, useSceneDelete } from "../../api/generated/scene/scene"
import { useSessionUpdateUserProfile } from "../../api/generated/session/session"
import { stateQueryKey, useStateQuery } from "../../api/state"
import { useConfirmDialog } from "../../shared/ConfirmDialog"
import { Checkbox } from "../../shared/Checkbox"
import { DeleteIcon, ThemeIcon } from "../../shared/icons"
import { SettingsAction } from "../../shared/SettingsAction"
import { useTheme } from "../../shared/hooks/useTheme"
import { errorText } from "../../shared/imageUtils"
import { useOptionsParams } from "./routes"

export function GeneralPanel() {
  const queryClient = useQueryClient()
  const { data } = useStateQuery()
  const { toggleTheme } = useTheme()
  const confirm = useConfirmDialog()
  const options = useOptionsParams()
  const updateProfile = useSessionUpdateUserProfile({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: stateQueryKey })
      },
    },
  })
  const deleteNpcMutation = useNpcDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: stateQueryKey })
      },
    },
  })
  const resetNpc = useNpcResetActive({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: stateQueryKey })
      },
    },
  })
  const [profile, setProfile] = useState("")
  const [deleteNpc, setDeleteNpc] = useState(false)
  const [deleteScene, setDeleteScene] = useState(false)
  const [deleteContext, setDeleteContext] = useState(false)
  const contextChecked = deleteContext || deleteNpc
  const deleteSceneMutation = useSceneDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: stateQueryKey })
        void queryClient.invalidateQueries({ queryKey: getSceneListOptionsQueryKey() })
      },
    },
  })
  const busy = updateProfile.isPending || resetNpc.isPending || deleteNpcMutation.isPending || deleteSceneMutation.isPending
  const error = errorText(updateProfile.error || resetNpc.error || deleteNpcMutation.error || deleteSceneMutation.error, "")

  useEffect(() => setProfile(data?.userProfile || ""), [data?.npcId, data?.sceneId, data?.userProfile])
  useEffect(() => {
    if (!data?.isDynamicNpc) setDeleteNpc(false)
  }, [data?.isDynamicNpc])
  useEffect(() => {
    if (!data?.isDynamicScene) setDeleteScene(false)
  }, [data?.isDynamicScene])

  async function reset() {
    const parts = ["Verlauf"]
    if (deleteNpc && data?.isDynamicNpc) parts.push("erstellter NPC")
    if (deleteScene && data?.isDynamicScene) parts.push("erstellte Szene")
    if (contextChecked) parts.push("NPC-Kontext")
    const accepted = await confirm({
      title: "Verlauf löschen",
      message: "Sollen folgende Dinge gelöscht werden?",
      listItems: parts,
      confirmLabel: "Löschen",
      danger: true,
    })
    if (!accepted) return
    const npc = data?.npcId
    const scene = data?.sceneId
    if (deleteScene && scene) {
      await deleteSceneMutation.mutateAsync({ scene })
    }
    if (deleteNpc && npc) {
      await deleteNpcMutation.mutateAsync({ npc })
    } else if (!deleteScene && npc) {
      await resetNpc.mutateAsync({ npc })
    }
    options.close()
  }

  return (
    <>
      <section className="sg-settings-section">
        <h3 className="sg-settings-heading">Allgemein</h3>
        <div className="sg-settings-actions">
          <SettingsAction icon={<ThemeIcon />} title="Theme wechseln" description="Zwischen hellem und dunklem Design wechseln" disabled={busy} onClick={toggleTheme} />
          <SettingsAction icon={<DeleteIcon />} title="Verlauf löschen" description="Entfernt Nachrichten und Bilder der aktiven Konversation" danger disabled={busy} onClick={reset} />
          <Checkbox label="Erstellten NPC mit löschen" checked={deleteNpc} disabled={busy || !data?.isDynamicNpc} onChange={setDeleteNpc} />
          <Checkbox label="Erstellte Szene mit löschen" checked={deleteScene} disabled={busy || !data?.isDynamicScene} onChange={setDeleteScene} />
          <Checkbox label="Erstellten NPC-Kontext löschen" checked={contextChecked} disabled={busy || deleteNpc} onChange={setDeleteContext} />
        </div>
        {error ? <div className="sg-scene-error">{error}</div> : null}
      </section>
      <section className="sg-settings-section">
        <h3 className="sg-selector-legend">Dein Profil</h3>
        <textarea className="sg-settings-textarea chat-scrollbar" placeholder="Was soll der NPC über dich wissen? (Name, Beruf, Geschlecht)" aria-label="User Profile editieren" value={profile} disabled={busy} onChange={(event) => setProfile(event.currentTarget.value)} onBlur={() => updateProfile.mutate({ data: { content: profile.trim() } })} />
      </section>
    </>
  )
}
