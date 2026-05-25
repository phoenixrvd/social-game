import type { ReactNode } from "react"
import { ContextIcon, GeneralIcon, ImageIcon, SaveIcon } from "../../shared/icons"
import { ContextPanel } from "./ContextPanel"
import { EntityCreator } from "../entities/EntityCreator"
import { GeneralPanel } from "./GeneralPanel"
import { HistoryPanel } from "./HistoryPanel"
import { ImagePanel } from "./ImagePanel"
import { SceneContextPanel } from "./SceneContextPanel"
import { type OptionPanel, useOptionsParams } from "./routes"

type OptionsShellProps = {
  activePanel: OptionPanel
}

const TABS: { id: OptionPanel; icon: ReactNode; label: string }[] = [
  { id: "context", icon: <ContextIcon />, label: "Kontext" },
  { id: "image", icon: <ImageIcon />, label: "Bild" },
  { id: "history", icon: <SaveIcon />, label: "Zwischenstände" },
  { id: "general", icon: <GeneralIcon />, label: "Allgemein" },
]

export function OptionsShell({ activePanel }: OptionsShellProps) {
  const options = useOptionsParams()

  return (
    <div id="sg-options-panel" className="sg-options-panel">
      <div className="sg-options-tab-panels">
        <div id={`sg-options-tab-panel-${activePanel}`} className="sg-options-tab-panel" role="tabpanel" data-option={activePanel}>
          <ActivePanel panel={activePanel} />
        </div>
      </div>
      <div className="sg-options-tabs-list" role="tablist" aria-label="Optionen">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className="sg-options-tab"
            role="tab"
            id={`sg-options-tab-${tab.id}`}
            aria-label={tab.label}
            aria-selected={activePanel === tab.id ? "true" : "false"}
            aria-controls={`sg-options-tab-panel-${tab.id}`}
            tabIndex={activePanel === tab.id ? 0 : -1}
            onClick={() => options.navigateToPanel(tab.id)}
          >
            {tab.icon}
          </button>
        ))}
      </div>
    </div>
  )
}

function ActivePanel({ panel }: { panel: OptionPanel }) {
  if (panel === "context") return <ContextPanel />
  if (panel === "image") return <ImagePanel />
  if (panel === "history") return <HistoryPanel />
  if (panel === "general") return <GeneralPanel />
  if (panel === "scene-creator") return <EntityCreator type="scene" />
  if (panel === "npc-creator") return <EntityCreator type="npc" />
  return <SceneContextPanel />
}
