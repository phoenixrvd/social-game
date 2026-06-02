import { useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { useAppView } from "../../state/appView"
import { buildOptionsPath, isOptionPanel, type OptionPanel } from "./optionsRoutes"
import { OptionsShellContainer } from "./OptionsShellContainer"

export function OptionsRouteContainer() {
  const params = useParams()
  const navigate = useNavigate()
  const { data: appView } = useAppView()
  const panel = isOptionPanel(params.panel) ? params.panel : "context"

  useEffect(() => {
    if (!params.npcId || !params.sceneId) return
    if (isOptionPanel(params.panel)) return
    navigate(buildOptionsPath(params.npcId, params.sceneId, "context"), { replace: true })
  }, [navigate, params.npcId, params.panel, params.sceneId])

  useEffect(() => {
    if (!params.npcId || !params.sceneId) return

    function closeOnOutsidePointer(event: PointerEvent) {
      const target = event.target
      if (!(target instanceof Element)) return
      if (target.closest(".sg-input-component")) return
      if (target.closest(".sg-confirm-backdrop")) return
      navigate(`/sg/${params.npcId}/${params.sceneId}`)
    }

    document.addEventListener("pointerdown", closeOnOutsidePointer)
    return () => document.removeEventListener("pointerdown", closeOnOutsidePointer)
  }, [navigate, params.npcId, params.sceneId])

  if (!appView || !params.npcId || !params.sceneId) return null
  return (
    <OptionsShellContainer
      activePanel={panel as OptionPanel}
      npcId={params.npcId}
      sceneId={params.sceneId}
      appView={appView}
    />
  )
}
