import { useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { streamChatReply } from "../../api/chat"
import { stateQueryKey } from "../../api/state"
import type { ChatMessage } from "../../api/types"

export function useChatStream() {
  const queryClient = useQueryClient()
  const [optimisticMessages, setOptimisticMessages] = useState<ChatMessage[]>([])
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState("")

  async function submit(text: string) {
    const message = text.trim()
    if (!message || isSending) return false

    const userId = `user-local-${Date.now()}`
    const assistantId = `assistant-local-${Date.now()}`
    setError("")
    setIsSending(true)
    setOptimisticMessages([{ id: userId, role: "user", content: message, timestamp_utc: new Date().toISOString() }])

    try {
      await streamChatReply(message, (delta) => {
        setOptimisticMessages((current) => appendAssistantChunk(current, assistantId, delta))
      })
      await queryClient.invalidateQueries({ queryKey: stateQueryKey })
      setOptimisticMessages([])
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nachricht konnte nicht gesendet werden.")
      setOptimisticMessages((current) => current.filter((item) => item.id !== assistantId || item.content?.trim()))
      return false
    } finally {
      setIsSending(false)
    }
  }

  return { optimisticMessages, isSending, error, submit }
}

function appendAssistantChunk(messages: ChatMessage[], assistantId: string, delta: string) {
  const assistant = messages.find((message) => message.id === assistantId)
  if (!assistant) {
    return [...messages, { id: assistantId, role: "assistant", content: delta, timestamp_utc: new Date().toISOString() }]
  }
  return messages.map((message) => message.id === assistantId ? { ...message, content: `${message.content || ""}${delta}` } : message)
}
