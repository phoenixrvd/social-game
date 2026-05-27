import { useEffect, useRef } from "react"
import { Outlet } from "react-router-dom"
import { useImageSignatureQuery, useStateQuery } from "../api/state"
import type { AppStateView } from "../api/types"
import { ChatPane } from "../features/chat/ChatPane"
import { Composer } from "../features/chat/Composer"
import { useChatStream } from "../features/chat/useChatStream"
import { SceneImage } from "../features/image/SceneImage"
import { useViewportHeightCssVar } from "../shared/hooks/useViewportHeightCssVar"

export function App() {
  useViewportHeightCssVar()
  const inputRef = useRef<HTMLTextAreaElement | null>(null)
  const stateQuery = useStateQuery()
  const state = stateQuery.data
  const imageSignatureQuery = useImageSignatureQuery(Boolean(state?.imageAutogenerate))
  const chat = useChatStream()

  useEffect(() => {
    const polledState = imageSignatureQuery.data
    if (!state || !polledState) return
    if (!hasImageStateChanged(state, polledState)) return
    void stateQuery.refetch()
  }, [
    state,
    stateQuery,
    imageSignatureQuery.data?.imageSignature,
    imageSignatureQuery.data?.imageIsOriginal,
    imageSignatureQuery.data?.videoUrl,
    imageSignatureQuery.data?.imageOriginalUrl,
    imageSignatureQuery.data?.imageBackups,
  ])

  return (
    <div className="app-viewport">
      <div className="sg-layout-root">
        <section className="sg-chat-pane" aria-label="Dialogbereich">
          <ChatPane messages={state?.messages ?? []} optimisticMessages={chat.optimisticMessages} />
          <Composer inputRef={inputRef} chat={chat} />
        </section>
        <section className="sg-scene-image-slot" aria-label="Szenenbild">
          <div className="sg-image-pane">
            {!state?.imageUrl ? <div className="sg-image-empty">Kein Bild geladen</div> : null}
            <SceneImage className="sg-scene-thumbnail" imageState={state} />
          </div>
        </section>
      </div>
      <Outlet />
    </div>
  )
}

function hasImageStateChanged(currentState: AppStateView, polledState: AppStateView): boolean {
  if (currentState.imageSignature !== polledState.imageSignature) return true
  if (currentState.imageIsOriginal !== polledState.imageIsOriginal) return true
  if (currentState.videoUrl !== polledState.videoUrl) return true
  if (currentState.imageOriginalUrl !== polledState.imageOriginalUrl) return true

  const currentBackups = currentState.imageBackups.map((backup) => `${backup.name}|${backup.signature || ""}`)
  const polledBackups = polledState.imageBackups.map((backup) => `${backup.name}|${backup.signature || ""}`)
  return currentBackups.join("||") !== polledBackups.join("||")
}
