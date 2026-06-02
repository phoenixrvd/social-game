import type { MessageResponse as ChatMessage } from "../api/generated/model"

export function appendAssistantChunk(messages: ChatMessage[], assistantId: string, delta: string) {
  const assistant = messages.find((message) => message.id === assistantId)
  if (!assistant) {
    return [
      ...messages,
      { id: assistantId, role: "assistant", content: delta, timestampUtc: new Date().toISOString() } as ChatMessage,
    ]
  }
  return messages.map((message) =>
    message.id === assistantId ? { ...message, content: `${message.content || ""}${delta}` } : message,
  )
}
