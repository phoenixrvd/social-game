import { useEffect, useRef } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { Outlet } from "react-router-dom"
import { stateQueryKey, useImageSignatureQuery, useStateQuery } from "../api/state"
import type { AppStateView } from "../api/state"
import { ChatPane } from "../features/chat/ChatPane"
import { Composer } from "../features/chat/Composer"
import { useChatStream } from "../features/chat/useChatStream"
import { SceneImage } from "../features/image/SceneImage"
import { useViewportHeightCssVar } from "../shared/hooks/useViewportHeightCssVar"

export function App() {
  useViewportHeightCssVar()
  const queryClient = useQueryClient()
  const inputRef = useRef<HTMLTextAreaElement | null>(null)
  const stateQuery = useStateQuery()
  const state = stateQuery.data
  const imageSignatureQuery = useImageSignatureQuery(Boolean(state?.imageAutogenerate))
  const stateWithImage = state ? ({ ...state, ...imageSignatureQuery.data } as AppStateView) : state
  const chat = useChatStream()

  useEffect(() => {
    const polledState = imageSignatureQuery.data
    if (!state || !polledState) return
    if (!hasImageStateChanged(state, polledState)) return
    queryClient.setQueryData(stateQueryKey, (current: unknown) => {
      if (!current || typeof current !== "object") return current
      return {
        ...current,
        imageSignature: polledState.imageSignature ?? null,
        imageIsOriginal: polledState.imageIsOriginal ?? true,
      }
    })
  }, [
    queryClient,
    state?.imageSignature,
    state?.imageIsOriginal,
    imageSignatureQuery.data?.imageSignature,
    imageSignatureQuery.data?.imageIsOriginal,
  ])

  return (
    <div className="app-viewport">
      <div className="sg-layout-root">
        <section className="sg-chat-pane" aria-label="Dialogbereich">
          <ChatPane messages={stateWithImage?.messages ?? []} optimisticMessages={chat.optimisticMessages} />
          <Composer inputRef={inputRef} chat={chat} appState={stateWithImage} isStateLoading={stateQuery.isLoading} />
        </section>
        <section className="sg-scene-image-slot" aria-label="Szenenbild">
          <div className="sg-image-pane">
            {!stateWithImage?.imageUrl ? <div className="sg-image-empty">Kein Bild geladen</div> : null}
            <SceneImage className="sg-scene-thumbnail" imageState={stateWithImage} />
          </div>
        </section>
      </div>
      <Outlet />
    </div>
  )
}

function hasImageStateChanged(currentState: AppStateView, polledState: Partial<AppStateView>): boolean {
  if (currentState.imageSignature !== polledState.imageSignature) return true
  if (currentState.imageIsOriginal !== polledState.imageIsOriginal) return true
  return false
}
