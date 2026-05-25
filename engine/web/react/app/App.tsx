import { useRef } from "react"
import { Outlet } from "react-router-dom"
import { useStateQuery } from "../api/state"
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
  const chat = useChatStream()

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
