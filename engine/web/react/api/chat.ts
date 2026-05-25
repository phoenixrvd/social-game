export type ChatStreamEvent =
  | { type: "chunk"; delta?: string }
  | { type: "done" }
  | { type: "error"; detail?: string }

export async function streamChatReply(
  message: string,
  onChunk: (delta: string) => void,
): Promise<void> {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  })

  if (!response.ok || !response.body) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: unknown }
    throw new Error(typeof payload.detail === "string" ? payload.detail : "Nachricht konnte nicht gesendet werden.")
  }

  await readStream(response.body, onChunk)
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

    if (done) break
  }

  if (!doneSeen) throw new Error("Nachricht wurde unvollstaendig uebertragen.")
}

function parseStreamEvent(line: string): ChatStreamEvent | null {
  if (!line) return null
  try {
    return JSON.parse(line) as ChatStreamEvent
  } catch {
    throw new Error("Ungueltige Streaming-Antwort vom Server.")
  }
}
