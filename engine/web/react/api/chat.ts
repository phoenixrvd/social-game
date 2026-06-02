import { chatStream } from "./generated/chat/chat"

export type ChatStreamEvent = { type: "chunk"; delta?: string } | { type: "done" } | { type: "error"; detail?: string }

export async function streamChatReply(message: string, onChunk: (delta: string) => void): Promise<void> {
  const response = await chatStream({ message }, { headers: { Accept: "application/x-ndjson" } })
  const stream = extractResponseBodyStream(response)
  if (!stream) throw new Error("Nachricht konnte nicht gesendet werden.")
  await readStream(stream, onChunk)
}

function extractResponseBodyStream(response: unknown): ReadableStream<Uint8Array> | null {
  if (!response || typeof response !== "object") return null

  if ("data" in response && (response as { data?: unknown }).data instanceof ReadableStream) {
    return (response as { data: ReadableStream<Uint8Array> }).data
  }

  const streamCandidate = (response as { stream?: { body?: unknown } }).stream
  if (streamCandidate?.body instanceof ReadableStream) {
    return streamCandidate.body as ReadableStream<Uint8Array>
  }

  return null
}

async function readStream(body: ReadableStream<Uint8Array>, onChunk: (delta: string) => void) {
  const reader = body.getReader()
  const decoder = new TextDecoder("utf-8")
  let buffer = ""
  let doneSeen = false

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
    const lines = buffer.split("\n")
    buffer = lines.pop() || ""

    for (const line of lines) {
      const event = parseStreamEvent(line.trim())
      if (!event) continue
      if (event.type === "chunk" && event.delta) onChunk(event.delta)
      if (event.type === "done") doneSeen = true
      if (event.type === "error") throw new Error(event.detail || "Nachricht konnte nicht gesendet werden.")
    }

    if (done) {
      const lastLine = buffer.trim()
      if (lastLine) {
        const event = parseStreamEvent(lastLine)
        if (event?.type === "chunk" && event.delta) onChunk(event.delta)
        if (event?.type === "done") doneSeen = true
        if (event?.type === "error") throw new Error(event.detail || "Nachricht konnte nicht gesendet werden.")
      }
      break
    }
  }

  if (!doneSeen) throw new Error("Nachricht wurde unvollständig übertragen.")
}

function parseStreamEvent(line: string): ChatStreamEvent | null {
  if (!line) return null
  try {
    return JSON.parse(line) as ChatStreamEvent
  } catch {
    throw new Error("Ungültige Streaming-Antwort vom Server.")
  }
}
