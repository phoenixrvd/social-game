import { useEffect, useState } from "react"
import { useUpdateUserProfileMutation } from "../../api/context"
import { useResetNpcMutation } from "../../api/session"
import { useStateQuery } from "../../api/state"
import { useConfirmDialog } from "../../shared/ConfirmDialog"
import { Checkbox } from "../../shared/Checkbox"
import { DeleteIcon, ThemeIcon } from "../../shared/icons"
import { SettingsAction } from "../../shared/SettingsAction"
import { useTheme } from "../../shared/hooks/useTheme"
import { errorText } from "../../shared/imageUtils"
import { useOptionsParams } from "./routes"

export function GeneralPanel() {
  const { data } = useStateQuery()
  const { toggleTheme } = useTheme()
  const confirm = useConfirmDialog()
  const options = useOptionsParams()
  const updateProfile = useUpdateUserProfileMutation()
  const resetNpc = useResetNpcMutation()
  const [profile, setProfile] = useState("")
  const [deleteNpc, setDeleteNpc] = useState(false)
  const [deleteScene, setDeleteScene] = useState(false)
  const [deleteContext, setDeleteContext] = useState(false)
  const contextChecked = deleteContext || deleteNpc || deleteScene
  const busy = updateProfile.isPending || resetNpc.isPending
  const error = errorText(updateProfile.error || resetNpc.error, "")

  useEffect(() => setProfile(data?.userProfile || ""), [data?.npcId, data?.sceneId, data?.userProfile])
  useEffect(() => {
    if (!data?.isDynamicNpc) setDeleteNpc(false)
    if (!data?.isDynamicScene) setDeleteScene(false)
  }, [data?.isDynamicNpc, data?.isDynamicScene])

  async function reset() {
    const parts = ["Verlauf"]
    if (deleteNpc && data?.isDynamicNpc) parts.push("erstellter NPC")
    if (deleteScene && data?.isDynamicScene) parts.push("erstellte Szene")
    if (contextChecked) parts.push("NPC-Kontext")
    const accepted = await confirm({ title: "Verlauf loeschen", message: `Sollen folgende Dinge geloescht werden?\n\n- ${parts.join("\n- ")}`, confirmLabel: "Loeschen", danger: true })
    if (!accepted) return
    await resetNpc.mutateAsync({ deleteNpc, deleteScene, deleteNpcContext: contextChecked })
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
          <Checkbox label="Erstellten NPC-Kontext löschen" checked={contextChecked} disabled={busy || deleteNpc || deleteScene} onChange={setDeleteContext} />
        </div>
        {error ? <div className="sg-scene-error">{error}</div> : null}
      </section>
      <section className="sg-settings-section">
        <h3 className="sg-selector-legend">Dein Profil</h3>
        <textarea className="sg-settings-textarea chat-scrollbar" placeholder="Was soll der NPC über dich wissen? (Name, Beruf, Geschlecht)" aria-label="User Profile editieren" value={profile} disabled={busy} onChange={(event) => setProfile(event.currentTarget.value)} onBlur={() => updateProfile.mutate(profile.trim())} />
      </section>
    </>
  )
}
