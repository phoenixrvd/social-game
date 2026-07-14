import { useEffect, useState } from "react"
import { useAppCommands } from "../../../state/appCommands"
import type { AppView } from "../../../state/appViewTypes"
import { SceneContextPanelView } from "./SceneContextPanelView"

export function SceneContextPanelContainer({ appView }: { appView: AppView }) {
  const commands = useAppCommands()
  const [content, setContent] = useState("")
  useEffect(() => {
    setContent(appView.scene.context)
  }, [appView.session.npcId, appView.session.sceneId, appView.scene.context])

  async function generate() {
    setContent(await commands.generateSceneContext({ content }))
  }

  return <SceneContextPanelView content={content} commands={commands} onContent={setContent} onGenerate={generate} />
}
