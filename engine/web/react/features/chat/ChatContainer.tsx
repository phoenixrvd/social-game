import type { AppView } from "../../state/appViewTypes"
import type { ChatCommands } from "./chatCommands"
import { ChatView } from "./ChatView"

type ChatContainerProps = {
  appView?: AppView
  chat: ChatCommands
}

export function ChatContainer({ appView, chat }: ChatContainerProps) {
  return <ChatView messages={appView?.chat.messages ?? []} optimisticMessages={chat.optimisticMessages} />
}
