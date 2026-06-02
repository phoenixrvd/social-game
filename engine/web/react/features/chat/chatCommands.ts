import { useRef, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { streamChatReply } from "../../api/chat"
import type { MessageResponse as ChatMessage } from "../../api/generated/model"
import { MessageResponseRole } from "../../api/generated/model"
import { getSessionGetStateQueryKey } from "../../api/generated/session/session"
import { appendAssistantChunk } from "../../state/optimistic"

export function useChatCommands() {
  const queryClient = useQueryClient()
  const [optimisticMessages, setOptimisticMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState("")
  const startedAtRef = useRef<number | null>(null)

  async function sendMessage(text: string): Promise<void> {
    const message = text.trim()
    if (!message || shouldIgnoreSend(isStreaming, startedAtRef.current)) return
    const userId = `user-local-${Date.now()}`
    const assistantId = `assistant-local-${Date.now()}`
    setError("")
    startedAtRef.current = Date.now()
    setIsStreaming(true)
    setOptimisticMessages([
      { id: userId, role: MessageResponseRole.user, content: message, timestampUtc: new Date().toISOString() },
    ])

    try {
      await streamChatReply(message, (delta) =>
        setOptimisticMessages((current) => appendAssistantChunk(current, assistantId, delta)),
      )
      await queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() })
      setOptimisticMessages([])
    } catch (err) {
      const nextError = err instanceof Error ? err.message : "Nachricht konnte nicht gesendet werden."
      setError(nextError || "Nachricht konnte nicht gesendet werden.")
      setOptimisticMessages((current) => current.filter((item) => item.id !== assistantId || item.content?.trim()))
      throw err
    } finally {
      startedAtRef.current = null
      setIsStreaming(false)
    }
  }

  return { optimisticMessages, isStreaming, error, sendMessage }
}

function shouldIgnoreSend(isStreaming: boolean, startedAt: number | null): boolean {
  return isStreaming && startedAt !== null && Date.now() - startedAt <= 20000
}

export type ChatCommands = ReturnType<typeof useChatCommands>
