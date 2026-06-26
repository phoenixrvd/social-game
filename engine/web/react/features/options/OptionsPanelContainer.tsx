import type { ComponentType } from "react"
import type { AppView } from "../../state/appViewTypes"
import { EntityEditorContainer } from "../entities/EntityEditorContainer"
import type { OptionPanel } from "./optionsRoutes"
import { ContextPanelContainer } from "./panels/ContextPanelContainer"
import { GeneralPanelContainer } from "./panels/GeneralPanelContainer"
import { HistoryPanelContainer } from "./panels/HistoryPanelContainer"
import { ImagePanelContainer } from "./panels/ImagePanelContainer"
import { SceneContextPanelContainer } from "./panels/SceneContextPanelContainer"

type OptionsPanelContainerProps = {
  activePanel: OptionPanel
  appView: AppView
  close: () => void
}

type PanelComponentProps = {
  appView: AppView
  close: () => void
}

const PANEL_COMPONENTS: Record<OptionPanel, ComponentType<PanelComponentProps>> = {
  context: ({ appView }) => <ContextPanelContainer appView={appView} />,
  image: ({ appView, close }) => <ImagePanelContainer appView={appView} close={close} />,
  history: () => <HistoryPanelContainer />,
  general: ({ appView, close }) => <GeneralPanelContainer appView={appView} close={close} />,
  "scene-creator": ({ appView }) => <EntityEditorContainer type="scene" mode="create" appView={appView} />,
  "scene-editor": ({ appView, close }) => (
    <EntityEditorContainer type="scene" mode="edit" appView={appView} close={close} />
  ),
  "npc-creator": ({ appView }) => <EntityEditorContainer type="npc" mode="create" appView={appView} />,
  "scene-context": ({ appView }) => <SceneContextPanelContainer appView={appView} />,
}

export function OptionsPanelContainer({ activePanel, appView, close }: OptionsPanelContainerProps) {
  const PanelComponent = PANEL_COMPONENTS[activePanel]
  return <PanelComponent appView={appView} close={close} />
}
