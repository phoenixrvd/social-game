import { useLayoutEffect, useRef } from "react"
import type { MessageResponse as ChatMessage } from "../../api/generated/model"
import type { MessageView as MessageViewModel } from "../../state/appViewTypes"
import { MessageListView } from "./MessageListView"

type ChatViewProps = {
  messages: MessageViewModel[]
  optimisticMessages: ChatMessage[]
}

export function ChatView({ messages, optimisticMessages }: ChatViewProps) {
  const listRef = useRef<HTMLDivElement | null>(null)
  const mergedMessages = [...messages, ...optimisticMessages]

  useLayoutEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "instant" })
  }, [mergedMessages.length, optimisticMessages.at(-1)?.content])

  return (
    <div className="sg-chat-component">
      <MessageListView listRef={listRef} messages={mergedMessages} />
    </div>
  )
}
