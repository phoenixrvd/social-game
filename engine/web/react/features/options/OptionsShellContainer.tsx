import { useNavigate } from "react-router-dom"
import type { AppView } from "../../state/appViewTypes"
import type { OptionPanel } from "./optionsRoutes"
import { OptionsPanelContainer } from "./OptionsPanelContainer"
import { OptionsShellView } from "./OptionsShellView"

type OptionsShellContainerProps = {
  activePanel: OptionPanel
  npcId: string
  sceneId: string
  appView: AppView
}

export function OptionsShellContainer(props: OptionsShellContainerProps) {
  const navigate = useNavigate()
  const close = () => navigate(`/sg/${props.npcId}/${props.sceneId}`)
  return (
    <OptionsShellView
      activePanel={props.activePanel}
      npcId={props.npcId}
      sceneId={props.sceneId}
      panel={<OptionsPanelContainer activePanel={props.activePanel} appView={props.appView} close={close} />}
    />
  )
}
