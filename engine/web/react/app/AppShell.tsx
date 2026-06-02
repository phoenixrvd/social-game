import type { RefObject } from "react"
import { Outlet } from "react-router-dom"
import type { AppView } from "../state/appViewTypes"
import type { ChatCommands } from "../features/chat/chatCommands"
import { ChatContainer } from "../features/chat/ChatContainer"
import { ComposerContainer } from "../features/chat/ComposerContainer"
import { SceneImageContainer } from "../features/image/SceneImageContainer"

type AppShellProps = {
  appView?: AppView
  chat: ChatCommands
  inputRef: RefObject<HTMLTextAreaElement | null>
  isLoading: boolean
}

export function AppShell({ appView, chat, inputRef, isLoading }: AppShellProps) {
  return (
    <div className="app-viewport">
      <div className="sg-layout-root">
        <section className="sg-chat-pane" aria-label="Dialogbereich">
          <ChatContainer appView={appView} chat={chat} />
          <ComposerContainer
            inputRef={inputRef}
            appView={appView}
            chat={chat}
            isStateLoading={isLoading}
            optionsPanel={<Outlet />}
          />
        </section>
        <section className="sg-scene-image-slot" aria-label="Szenenbild">
          <div className="sg-image-pane">
            {!appView?.image.url ? <div className="sg-image-empty">Kein Bild geladen</div> : null}
            <SceneImageContainer className="sg-scene-thumbnail" appView={appView} />
          </div>
        </section>
      </div>
    </div>
  )
}
