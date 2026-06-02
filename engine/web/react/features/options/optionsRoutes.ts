import { generatePath } from "react-router-dom"

export const OPTIONS_PANELS = [
  "context",
  "image",
  "history",
  "general",
  "scene-creator",
  "scene-editor",
  "npc-creator",
  "scene-context",
] as const

export const OPTIONS_ROUTE_PATTERN = "/sg/:npcId/:sceneId/options/:panel"

export type OptionPanel = (typeof OPTIONS_PANELS)[number]

export function isOptionPanel(value: string | undefined): value is OptionPanel {
  return Boolean(value && OPTIONS_PANELS.includes(value as OptionPanel))
}

export function buildOptionsPath(npcId: string, sceneId: string, panel: OptionPanel = "context") {
  return generatePath(OPTIONS_ROUTE_PATTERN, { npcId, sceneId, panel })
}
