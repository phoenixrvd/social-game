import { useEffect, useRef } from "react"
import { useMatch, useNavigate } from "react-router-dom"
import { useImageCurrentSignature } from "../api/generated/session/session"
import { useChatCommands } from "../features/chat/chatCommands"
import { useAppCommands } from "../state/appCommands"
import { useAppView } from "../state/appView"
import type { AppView } from "../state/appViewTypes"
import { useViewportHeightCssVar } from "../shared/hooks/useViewportHeightCssVar"
import { AppShell } from "./AppShell"

export function AppContainer() {
  useViewportHeightCssVar()
  const inputRef = useRef<HTMLTextAreaElement | null>(null)
  const appViewQuery = useAppView()
  const appView = appViewQuery.data
  const commands = useAppCommands()
  const chat = useChatCommands()
  useRouteSessionSync(appView, commands)
  useImagePolling(appView, appViewQuery.refetch)

  return <AppShell appView={appView} chat={chat} inputRef={inputRef} isLoading={appViewQuery.isLoading} />
}

function useRouteSessionSync(appView: AppView | undefined, commands: ReturnType<typeof useAppCommands>) {
  const nestedRouteMatch = useMatch("/sg/:npcId/:sceneId/*")
  const baseRouteMatch = useMatch("/sg/:npcId/:sceneId")
  const routeMatch = nestedRouteMatch ?? baseRouteMatch
  const npcId = routeMatch?.params.npcId
  const sceneId = routeMatch?.params.sceneId
  const navigate = useNavigate()
  const requestedSessionKey = useRef<string | null>(null)

  useEffect(() => {
    if (!appView) return
    if (!npcId || !sceneId) {
      navigate(`/sg/${appView.session.npcId}/${appView.session.sceneId}`, { replace: true })
      return
    }

    const validNpc = appView.npc.options.some((npc) => npc.id === npcId)
    const validScene = appView.scene.options.some((scene) => scene.id === sceneId)
    if (!validNpc || !validScene) {
      navigate(`/sg/${appView.session.npcId}/${appView.session.sceneId}`, { replace: true })
      return
    }

    const routeSessionKey = `${npcId}::${sceneId}`
    if (appView.session.npcId === npcId && appView.session.sceneId === sceneId) {
      requestedSessionKey.current = null
      return
    }
    if (commands.pending.session || requestedSessionKey.current === routeSessionKey) return
    requestedSessionKey.current = routeSessionKey
    void commands.selectContext({ npc: npcId, scene: sceneId }).catch(() => {
      requestedSessionKey.current = null
      navigate(`/sg/${appView.session.npcId}/${appView.session.sceneId}`, { replace: true })
    })
  }, [appView, commands, navigate, npcId, sceneId])
}

function useImagePolling(appView: AppView | undefined, refetchAppView: () => unknown) {
  const signatureQuery = useImageCurrentSignature({
    query: {
      enabled: Boolean(appView?.image.autogenerate),
      refetchInterval: appView?.image.autogenerate ? 5000 : false,
    },
    request: { cache: "no-store" },
  })

  useEffect(() => {
    const signature = signatureQuery.data?.status === 200 ? signatureQuery.data.data.signature : null
    if (!appView || !signature) return
    if (signature === appView.image.signature) return
    void refetchAppView()
  }, [appView, refetchAppView, signatureQuery.data])
}
