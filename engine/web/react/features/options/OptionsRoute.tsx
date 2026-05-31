import { useEffect, useRef } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { useSessionUpdateSession } from "../../api/generated/session/session"
import { normalizeStateDynamic, stateQueryKey, useStateQuery } from "../../api/state"
import { OptionsShell } from "./OptionsShell"
import { buildOptionsPath, isOptionPanel, useOptionsParams } from "./routes"

export function OptionsRoute() {
  const queryClient = useQueryClient()
  const options = useOptionsParams()
  const navigate = useNavigate()
  const { data } = useStateQuery()
  const updateSession = useSessionUpdateSession({
    mutation: {
      onSuccess: (response) => {
        queryClient.setQueryData(stateQueryKey, normalizeStateDynamic(response.data))
      },
    },
  })
  const updateSessionPending = updateSession.isPending
  const mutateSession = updateSession.mutate
  const requestedSessionKey = useRef<string | null>(null)

  useEffect(() => {
    if (!options.isOptionsRoute || !options.npcId || !options.sceneId) return
    if (!isOptionPanel(options.rawPanel)) {
      navigate(buildOptionsPath(options.npcId, options.sceneId, "context"), { replace: true })
      return
    }
    const routeSessionKey = `${options.npcId}::${options.sceneId}`
    if (data?.npcId === options.npcId && data.sceneId === options.sceneId) {
      requestedSessionKey.current = null
      return
    }
    if (updateSessionPending || requestedSessionKey.current === routeSessionKey) return
    requestedSessionKey.current = routeSessionKey
    mutateSession(
      { data: { npc: options.npcId, scene: options.sceneId } },
      { onError: () => { requestedSessionKey.current = null } },
    )
  }, [data?.npcId, data?.sceneId, mutateSession, navigate, options.isOptionsRoute, options.npcId, options.rawPanel, options.sceneId, updateSessionPending])

  if (!options.isOptionsRoute) return null
  return <OptionsShell activePanel={options.panel} />
}
