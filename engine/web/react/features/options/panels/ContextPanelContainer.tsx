import type { AppView } from "../../../state/appViewTypes"
import { ContextPanelView } from "./ContextPanelView"

export function ContextPanelContainer({ appView }: { appView: AppView }) {
  return <ContextPanelView appView={appView} />
}
