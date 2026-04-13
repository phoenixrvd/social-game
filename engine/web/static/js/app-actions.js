import { appStore } from "./app-store.js"

let imagePollTimer = null

function createNowTimestamp() {
  return new Date().toISOString()
}

function appendCacheBuster(url) {
  if (!url) {
    return null
  }
  const separator = url.includes("?") ? "&" : "?"
  return `${url}${separator}t=${Date.now()}`
}

async function readJsonResponse(response) {
  return response.json().catch(() => ({}))
}

function getErrorMessage(payload, fallbackMessage) {
  if (typeof payload?.detail === "string" && payload.detail.trim()) {
    return payload.detail.trim()
  }
  return fallbackMessage
}

function parseChatStreamEvent(line) {
  try {
    return JSON.parse(line)
  } catch {
    throw new Error("Ungueltige Streaming-Antwort vom Server.")
  }
}

function waitForNextPaint() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve())
  })
}

function mapStatePayload(payload = {}) {
  return {
    messages: Array.isArray(payload.messages) ? payload.messages : [],
    imageUrl: payload.image_url ? appendCacheBuster(payload.image_url) : null,
    imageSignature: typeof payload.image_signature === "string" ? payload.image_signature : null,
    npcs: Array.isArray(payload.npcs) ? payload.npcs : [],
    scenes: Array.isArray(payload.scenes) ? payload.scenes : [],
    npcId: typeof payload.npc_id === "string" ? payload.npc_id : null,
    sceneId: typeof payload.scene_id === "string" ? payload.scene_id : null,
  }
}

function startImagePolling(intervalMs = 5000) {
  if (imagePollTimer !== null) {
    clearInterval(imagePollTimer)
  }
  imagePollTimer = setInterval(() => {
    pollImageSignature()
  }, intervalMs)
}

function canPollImage(state) {
  return !state.isSending && !state.isSessionLoading && !state.isImageRefreshLoading
}

async function pollImageSignature(force = false) {
  const state = appStore.getState()
  if (!force && !canPollImage(state)) {
    return
  }

  const response = await fetch("/api/image/signature", { cache: "no-store" }).catch(() => null)
  if (!response?.ok) {
    return
  }

  const payload = await response.json().catch(() => ({}))
  const signature = typeof payload.signature === "string" ? payload.signature : null
  if (!signature || signature === state.imageSignature) {
    return
  }

  appStore.setState({
    imageSignature: signature,
    imageUrl: appendCacheBuster(typeof payload.image_url === "string" ? payload.image_url : state.imageUrl),
  })
}

async function loadInitialState() {
  appStore.setState({ isSessionLoading: true })
  try {
    const response = await fetch("/api/state", { cache: "no-store" })
    const payload = await readJsonResponse(response)
    if (!response.ok) {
      appStore.setState({ errorMessage: getErrorMessage(payload, "State konnte nicht geladen werden.") })
      return
    }
    appStore.setState(mapStatePayload(payload))
  } catch (error) {
    appStore.setState({ errorMessage: error instanceof Error ? error.message : "Backend nicht erreichbar." })
  } finally {
    appStore.setState({ isSessionLoading: false, focusRequestedAt: Date.now() })
    startImagePolling()
  }
}

async function updateSession(nextSession = {}) {
  if (appStore.getState().isSending) {
    return
  }

  appStore.setState({ isSessionLoading: true })
  try {
    const response = await fetch("/api/session", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(nextSession),
    })
    const payload = await readJsonResponse(response)
    if (!response.ok) {
      appStore.setState({ errorMessage: getErrorMessage(payload, "Session konnte nicht aktualisiert werden.") })
      return
    }
    appStore.setState(mapStatePayload(payload))
  } catch (error) {
    appStore.setState({ errorMessage: error instanceof Error ? error.message : "Session konnte nicht aktualisiert werden." })
  } finally {
    appStore.setState({ isSessionLoading: false })
  }
}

async function refreshImage() {
  const state = appStore.getState()
  if (state.isSending || state.isSessionLoading) {
    return
  }

  appStore.setState({ isImageRefreshLoading: true })
  await waitForNextPaint()

  try {
    const response = await fetch("/api/image/refresh-active", { method: "POST" })
    const payload = await readJsonResponse(response)
    if (!response.ok) {
      appStore.setState({ errorMessage: getErrorMessage(payload, "Bild konnte nicht aktualisiert werden.") })
      return
    }

    appStore.setState({ imageUrl: appendCacheBuster("/api/image/current") })
    await pollImageSignature(true)
  } catch (error) {
    appStore.setState({ errorMessage: error instanceof Error ? error.message : "Bild konnte nicht aktualisiert werden." })
  } finally {
    appStore.setState({ isImageRefreshLoading: false })
  }
}

async function resetNpc() {
  const state = appStore.getState()
  if (state.isSending || state.isSessionLoading) {
    return
  }

  if (!window.confirm("Soll der Verlauf des aktiven NPC wirklich geloescht werden?")) {
    return
  }

  appStore.setState({ isSessionLoading: true })
  try {
    const response = await fetch("/api/npc/reset-active", { method: "DELETE" })
    const payload = await readJsonResponse(response)
    if (!response.ok) {
      appStore.setState({ errorMessage: getErrorMessage(payload, "Verlauf konnte nicht geloescht werden.") })
      return
    }
    appStore.setState(mapStatePayload(payload))
  } catch (error) {
    appStore.setState({ errorMessage: error instanceof Error ? error.message : "Verlauf konnte nicht geloescht werden." })
  } finally {
    appStore.setState({ isSessionLoading: false })
  }
}

function handleChatStreamEvent(event, assistantId) {
  if (!event || typeof event.type !== "string") {
    throw new Error("Ungueltige Streaming-Antwort vom Server.")
  }

  if (event.type === "chunk") {
    const delta = typeof event.delta === "string" ? event.delta : ""
    const state = appStore.getState()
    appStore.setState({
      messages: state.messages.map((message) => {
        if (message.id !== assistantId) {
          return message
        }
        return { ...message, content: `${message.content || ""}${delta}` }
      }),
    })
    return false
  }

  if (event.type === "done") {
    return true
  }

  if (event.type === "error") {
    throw new Error(getErrorMessage(event, "Nachricht konnte nicht gesendet werden."))
  }

  throw new Error("Ungueltige Streaming-Antwort vom Server.")
}

async function streamAssistantReply(text, assistantId) {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  })

  if (!response.ok || !response.body) {
    throw new Error(getErrorMessage(await readJsonResponse(response), "Nachricht konnte nicht gesendet werden."))
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder("utf-8")
  let buffer = ""
  let isDone = false

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })

    let newlineIndex = buffer.indexOf("\n")
    while (newlineIndex !== -1) {
      const line = buffer.slice(0, newlineIndex).trim()
      buffer = buffer.slice(newlineIndex + 1)
      if (line) {
        isDone = handleChatStreamEvent(parseChatStreamEvent(line), assistantId) || isDone
      }
      newlineIndex = buffer.indexOf("\n")
    }

    if (done) {
      break
    }
  }

  const trailingLine = buffer.trim()
  if (trailingLine) {
    isDone = handleChatStreamEvent(parseChatStreamEvent(trailingLine), assistantId) || isDone
  }

  if (!isDone) {
    throw new Error("Nachricht wurde unvollstaendig uebertragen.")
  }
}

async function submitMessage(payload = {}) {
  const state = appStore.getState()
  const submittedText = typeof payload === "string" ? payload : payload?.message
  const text = typeof submittedText === "string" ? submittedText.trim() : String(state.input || "").trim()
  if (!text || state.isSending || state.isSessionLoading) {
    return
  }

  const assistantId = `assistant-local-${Date.now()}`
  const messages = state.messages.filter((message) => !String(message?.id || "").startsWith("context-"))
  messages.push({ id: `user-${Date.now()}`, role: "user", content: text, timestamp: createNowTimestamp() })
  messages.push({ id: assistantId, role: "assistant", content: "", timestamp: createNowTimestamp() })
  appStore.setState({
    messages,
    input: "",
    isSending: true,
    isAssistantTyping: true,
    activeAssistantId: assistantId,
  })

  try {
    await streamAssistantReply(text, assistantId)
  } catch (error) {
    const latestState = appStore.getState()
    const assistantMessage = latestState.messages.find((message) => message.id === assistantId)
    if (!assistantMessage?.content?.trim()) {
      appStore.setState({ messages: latestState.messages.filter((message) => message.id !== assistantId) })
    }
    appStore.setState({
      errorMessage: error instanceof Error ? error.message : "Nachricht konnte nicht gesendet werden.",
    })
  } finally {
    appStore.setState({ isSending: false, isAssistantTyping: false, activeAssistantId: null })
  }
}

function toggleTheme() {
  const nextTheme = appStore.getState().theme === "dark" ? "light" : "dark"
  localStorage.setItem("theme", nextTheme)
  document.documentElement.setAttribute("data-theme", nextTheme)
  appStore.setState({ theme: nextTheme })
}

function setInput(value = "") {
  appStore.setState({ input: typeof value === "string" ? value : "" })
}

function toggleSelectorPanel() {
  appStore.setState({ isSelectorPanelOpen: !appStore.getState().isSelectorPanelOpen })
}

function toggleImageExpand(expanded = false) {
  const nextExpanded = Boolean(expanded)
  document.body.classList.toggle("sg-overflow-y-hidden", nextExpanded && window.matchMedia("(max-width: 1023px)").matches)
  appStore.setState({ isImageExpanded: nextExpanded })
}

function setImageError() {
  document.body.classList.toggle("sg-overflow-y-hidden", false)
  appStore.setState({ imageUrl: null, isImageExpanded: false })
}

export const appActions = {
  loadInitialState,
  submitMessage,
  updateSession,
  refreshImage,
  resetNpc,
  setInput,
  toggleTheme,
  toggleSelectorPanel,
  toggleImageExpand,
  setImageError,
}
