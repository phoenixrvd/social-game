import { useLayoutEffect, useRef } from "react"
import type { MessageResponse as ChatMessage } from "../../api/generated/model"
import { Message } from "./Message"

type ChatPaneProps = {
  messages: ChatMessage[]
  optimisticMessages?: ChatMessage[]
}

export function ChatPane({ messages, optimisticMessages = [] }: ChatPaneProps) {
  const listRef = useRef<HTMLDivElement | null>(null)
  const mergedMessages = [...messages, ...optimisticMessages]

  useLayoutEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "instant" })
  }, [mergedMessages.length, optimisticMessages.at(-1)?.content])

  return (
    <div className="sg-chat-component">
      <div
        className="sg-chat-messages chat-scrollbar sg-chat-messages-panel"
        role="log"
        aria-label="Chatverlauf"
        aria-live="polite"
        aria-relevant="additions"
        ref={listRef}
      >
        {mergedMessages.map((message, index) => (
          <Message key={message.id || `${message.role}-${index}`} message={message} />
        ))}
      </div>
    </div>
  )
}
