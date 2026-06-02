import type { ReactNode } from "react"
import { NavLink } from "react-router-dom"
import { ContextIcon, GeneralIcon, ImageIcon, SaveIcon } from "../../shared/icons"
import { buildOptionsPath, type OptionPanel } from "./optionsRoutes"

const TABS: { id: OptionPanel; icon: ReactNode; label: string }[] = [
  { id: "context", icon: <ContextIcon />, label: "Kontext" },
  { id: "image", icon: <ImageIcon />, label: "Bild" },
  { id: "history", icon: <SaveIcon />, label: "Zwischenstände" },
  { id: "general", icon: <GeneralIcon />, label: "Allgemein" },
]

type OptionsShellViewProps = {
  activePanel: OptionPanel
  npcId: string
  sceneId: string
  panel: ReactNode
}

export function OptionsShellView({ activePanel, npcId, sceneId, panel }: OptionsShellViewProps) {
  return (
    <div id="sg-options-panel" className="sg-options-panel">
      <div className="sg-options-tab-panels">
        <div
          id={`sg-options-tab-panel-${activePanel}`}
          className="sg-options-tab-panel"
          role="tabpanel"
          data-option={activePanel}
        >
          {panel}
        </div>
      </div>
      <div className="sg-options-tabs-list" role="tablist" aria-label="Optionen">
        {TABS.map((tab) => (
          <NavLink
            key={tab.id}
            className={({ isActive }) => `sg-options-tab${isActive ? " is-active" : ""}`}
            role="tab"
            id={`sg-options-tab-${tab.id}`}
            aria-label={tab.label}
            aria-selected={activePanel === tab.id ? "true" : "false"}
            aria-controls={`sg-options-tab-panel-${tab.id}`}
            tabIndex={activePanel === tab.id ? 0 : -1}
            to={buildOptionsPath(npcId, sceneId, tab.id)}
          >
            {tab.icon}
          </NavLink>
        ))}
      </div>
    </div>
  )
}
