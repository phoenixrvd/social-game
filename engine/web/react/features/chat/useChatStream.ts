import { useRef, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { streamChatReply } from "../../api/chat"
import type { MessageResponse as ChatMessage } from "../../api/generated/model"
import { MessageResponseRole } from "../../api/generated/model"
import { stateQueryKey } from "../../api/state"

export function useChatStream() {
  const queryClient = useQueryClient()
  const [optimisticMessages, setOptimisticMessages] = useState<ChatMessage[]>([])
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState("")
  const startedAtRef = useRef<number | null>(null)

  async function submit(text: string) {
    const message = text.trim()
    if (!message) return false
    if (isSending) {
      const startedAt = startedAtRef.current
      if (startedAt !== null && Date.now() - startedAt <= 20000) return false
    }

    const userId = `user-local-${Date.now()}`
    const assistantId = `assistant-local-${Date.now()}`
    setError("")
    startedAtRef.current = Date.now()
    setIsSending(true)
    setOptimisticMessages([{ id: userId, role: MessageResponseRole.user, content: message, timestampUtc: new Date().toISOString() }])

    try {
      await streamChatReply(message, (delta) => {
        setOptimisticMessages((current) => appendAssistantChunk(current, assistantId, delta))
      })
      await queryClient.invalidateQueries({ queryKey: stateQueryKey })
      setOptimisticMessages([])
      return true
    } catch (err) {
      const message = err instanceof Error ? err.message : "Nachricht konnte nicht gesendet werden."
      setError(message || "Nachricht konnte nicht gesendet werden.")
      setOptimisticMessages((current) => current.filter((item) => item.id !== assistantId || item.content?.trim()))
      return false
    } finally {
      startedAtRef.current = null
      setIsSending(false)
    }
  }

  return { optimisticMessages, isSending, error, submit }
}

function appendAssistantChunk(messages: ChatMessage[], assistantId: string, delta: string) {
  const assistant = messages.find((message) => message.id === assistantId)
  if (!assistant) {
    return [...messages, { id: assistantId, role: MessageResponseRole.assistant, content: delta, timestampUtc: new Date().toISOString() }]
  }
  return messages.map((message) => message.id === assistantId ? { ...message, content: `${message.content || ""}${delta}` } : message)
}
