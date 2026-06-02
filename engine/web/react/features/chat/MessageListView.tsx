import type { RefObject } from "react"
import type { MessageResponse as ChatMessage } from "../../api/generated/model"
import { MessageView } from "./MessageView"

type MessageListViewProps = {
  listRef: RefObject<HTMLDivElement | null>
  messages: ChatMessage[]
}

export function MessageListView({ listRef, messages }: MessageListViewProps) {
  return (
    <div
      className="sg-chat-messages chat-scrollbar sg-chat-messages-panel"
      role="log"
      aria-label="Chatverlauf"
      aria-live="polite"
      aria-relevant="additions"
      ref={listRef}
    >
      {messages.map((message, index) => (
        <MessageView key={message.id || `${message.role}-${index}`} message={message} />
      ))}
    </div>
  )
}
