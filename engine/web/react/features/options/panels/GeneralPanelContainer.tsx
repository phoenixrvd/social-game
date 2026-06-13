import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAppCommands } from "../../../state/appCommands"
import type { AppView } from "../../../state/appViewTypes"
import { useConfirmDialog } from "../../../shared/ConfirmDialog"
import { useTheme } from "../../../shared/hooks/useTheme"
import { buildOptionsPath } from "../optionsRoutes"
import { GeneralPanelView } from "./GeneralPanelView"

export function GeneralPanelContainer({ appView, close }: { appView: AppView; close: () => void }) {
  const commands = useAppCommands()
  const navigate = useNavigate()
  const { toggleTheme } = useTheme()
  const confirm = useConfirmDialog()
  const [deleteNpc, setDeleteNpc] = useState(false)
  const [deleteScene, setDeleteScene] = useState(false)
  const [deleteContext, setDeleteContext] = useState(false)

  useEffect(() => {
    if (!appView.npc.active?.isDynamicNpc) setDeleteNpc(false)
  }, [appView.npc.active?.isDynamicNpc])
  useEffect(() => {
    if (!appView.scene.active?.isDynamicScene) setDeleteScene(false)
  }, [appView.scene.active?.isDynamicScene])

  async function reset() {
    const contextChecked = deleteContext || deleteNpc
    const parts = ["Verlauf"]
    if (deleteNpc && appView.npc.active?.isDynamicNpc) parts.push("erstellter NPC")
    if (deleteScene && appView.scene.active?.isDynamicScene) parts.push("erstellte Szene")
    if (contextChecked) parts.push("NPC-Kontext")
    const accepted = await confirm({
      title: "Verlauf löschen",
      message: "Sollen folgende Dinge gelöscht werden?",
      listItems: parts,
      confirmLabel: "Löschen",
      danger: true,
    })
    if (!accepted) return
    if (deleteScene) await commands.deleteScene(appView.session.sceneId)
    if (deleteNpc) await commands.deleteNpc(appView.session.npcId)
    if (!deleteScene && !deleteNpc) await commands.resetNpc(appView.session.npcId)
    close()
  }

  return (
    <GeneralPanelView
      appView={appView}
      commands={commands}
      deleteNpc={deleteNpc}
      deleteScene={deleteScene}
      deleteContext={deleteContext || deleteNpc}
      onAvatarSelect={(avatar) => commands.selectContext({ avatar })}
      onAvatarEdit={() => navigate(buildOptionsPath(appView.session.npcId, appView.session.sceneId, "avatar-editor"))}
      onDeleteNpc={setDeleteNpc}
      onDeleteScene={setDeleteScene}
      onDeleteContext={setDeleteContext}
      onTheme={toggleTheme}
      onReset={reset}
    />
  )
}
