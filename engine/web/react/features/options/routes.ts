import { generatePath, useMatch, useNavigate, useParams } from "react-router-dom"

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

export function useOptionsParams() {
  const params = useParams()
  const routeMatch = useMatch(OPTIONS_ROUTE_PATTERN)
  const navigate = useNavigate()
  const panel = isOptionPanel(params.panel) ? params.panel : "context"
  const isOptionsRoute = Boolean(routeMatch)

  return {
    isOptionsRoute,
    npcId: params.npcId,
    sceneId: params.sceneId,
    rawPanel: params.panel,
    panel,
    close: () => navigate("/"),
    navigateToPanel: (nextPanel: OptionPanel) => {
      if (params.npcId && params.sceneId) navigate(buildOptionsPath(params.npcId, params.sceneId, nextPanel))
    },
    navigateToOptions: (npcId: string, sceneId: string, nextPanel: OptionPanel = panel) => navigate(buildOptionsPath(npcId, sceneId, nextPanel)),
  }
}
