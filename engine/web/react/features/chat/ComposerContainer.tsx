import { useLayoutEffect, useState } from "react"
import type { ReactNode, RefObject } from "react"
import { useLocation } from "react-router-dom"
import type { AppView } from "../../state/appViewTypes"
import { buildOptionsPath } from "../options/optionsRoutes"
import type { ChatCommands } from "./chatCommands"
import { ComposerView } from "./ComposerView"

type ComposerContainerProps = {
  inputRef: RefObject<HTMLTextAreaElement | null>
  appView?: AppView
  chat: ChatCommands
  isStateLoading: boolean
  optionsPanel: ReactNode
}

export function ComposerContainer({ inputRef, appView, chat, isStateLoading, optionsPanel }: ComposerContainerProps) {
  const location = useLocation()
  const [input, setInput] = useState("")
  const isOptionsOpen = location.pathname.includes("/options/")
  const npcId = appView?.session.npcId || appView?.session.defaultNpcId
  const sceneId = appView?.session.sceneId || appView?.session.defaultSceneId
  const optionsHref = npcId && sceneId ? buildOptionsPath(npcId, sceneId, "context") : "/"
  const toggleHref = isOptionsOpen ? `/sg/${npcId}/${sceneId}` : optionsHref

  useLayoutEffect(() => {
    const textarea = inputRef.current
    if (!textarea) return
    textarea.style.height = "auto"
    textarea.style.height = `${Math.max(textarea.scrollHeight, 46)}px`
  }, [input, inputRef])

  async function submit() {
    const text = input.trim()
    if (!text) return
    setInput("")
    await chat.sendMessage(text).catch(() => {})
  }

  return (
    <ComposerView
      input={input}
      inputRef={inputRef}
      isLoading={isStateLoading}
      isOptionsOpen={isOptionsOpen}
      isStreaming={chat.isStreaming}
      error={chat.error}
      optionsHref={toggleHref}
      appView={appView}
      optionsPanel={optionsPanel}
      onInput={setInput}
      onSubmit={submit}
    />
  )
}
