import { appStore } from "./app-store.js"

let imagePollTimer = null

const FIRST_OPEN_SELECTOR_STORAGE_KEY = "sg-first-open-selector-seen"

function createNowTimestamp() {
  return new Date().toISOString()
}

function isInstalledApp() {
  const standalone = window.matchMedia("(display-mode: standalone)").matches
  const fullscreen = window.matchMedia("(display-mode: fullscreen)").matches
  const minimalUi = window.matchMedia("(display-mode: minimal-ui)").matches

  return standalone || fullscreen || minimalUi || window.navigator.standalone === true
}

function getThemeColor(theme, installedApp) {
  if (!installedApp) {
    return theme === "light" ? "#f4f4f5" : "#18181b"
  }

  return theme === "light" ? "#f3f4f6" : "#09090b"
}

function syncThemeChrome(theme) {
  const installedApp = isInstalledApp()
  const themeColorMeta = document.querySelector("#theme-color-meta") || document.querySelector('meta[name="theme-color"]')

  document.documentElement.setAttribute("data-installed-app", installedApp ? "true" : "false")
  if (themeColorMeta) {
    themeColorMeta.setAttribute("content", getThemeColor(theme, installedApp))
  }
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
    throw new Error("Ungültige Streaming-Antwort vom Server.")
  }
}

function waitForNextPaint() {
  return new Promise((resolve) => {
    requestAnimationFrame(resolve)
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
    defaultSceneId: typeof payload.default_scene_id === "string" ? payload.default_scene_id : null,
    isDynamicScene: Boolean(payload.is_dynamic_scene),
    user_profile: typeof payload.user_profile === "string" ? payload.user_profile : "",
    imageAutogenerate: typeof payload.image_autogenerate === "boolean" ? payload.image_autogenerate : true,
  }
}

function hasSeenFirstOpenSelector() {
  return window.localStorage.getItem(FIRST_OPEN_SELECTOR_STORAGE_KEY) === "true"
}

function shouldOpenSelectorOnFirstLoad(payload = {}) {
  if (hasSeenFirstOpenSelector()) {
    return false
  }

  const hasNpcs = Array.isArray(payload.npcs) && payload.npcs.length > 0
  const hasScenes = Array.isArray(payload.scenes) && payload.scenes.length > 0
  if (!hasNpcs || !hasScenes) {
    return false
  }

  window.localStorage.setItem(FIRST_OPEN_SELECTOR_STORAGE_KEY, "true")
  return true
}

function appendAssistantChunk(messages, assistantId, assistantTimestamp, delta) {
  const assistantMessage = messages.find((message) => message.id === assistantId)
  if (!assistantMessage) {
    return [...messages, { id: assistantId, role: "assistant", content: delta, timestamp_utc: assistantTimestamp }]
  }

  return messages.map((message) => {
    if (message.id !== assistantId) {
      return message
    }
    return { ...message, content: `${message.content || ""}${delta}` }
  })
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
  const initialState = appStore.getState()
  if (!force && !canPollImage(initialState)) {
    return
  }

  const response = await fetch("/api/image/signature", { cache: "no-store" }).catch(() => null)
  if (!response?.ok) {
    return
  }

  const payload = await response.json().catch(() => ({}))
  const signature = typeof payload.signature === "string" ? payload.signature : null
  const latestState = appStore.getState()
  if (!force && !canPollImage(latestState)) {
    return
  }

  if (!signature || signature === latestState.imageSignature) {
    return
  }

  appStore.setState({
    imageSignature: signature,
    imageUrl: appendCacheBuster(typeof payload.image_url === "string" ? payload.image_url : latestState.imageUrl),
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

    const nextState = mapStatePayload(payload)
    appStore.setState({
      ...nextState,
      errorMessage: "",
      isSelectorPanelOpen: shouldOpenSelectorOnFirstLoad(payload),
    })
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
    appStore.setState({ ...mapStatePayload(payload), errorMessage: "" })
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

    appStore.setState({ imageUrl: appendCacheBuster("/api/image/current"), errorMessage: "" })
    await pollImageSignature(true)
  } catch (error) {
    appStore.setState({ errorMessage: error instanceof Error ? error.message : "Bild konnte nicht aktualisiert werden." })
  } finally {
    appStore.setState({ isImageRefreshLoading: false })
  }
}

async function revertImage() {
  const state = appStore.getState()
  if (state.isSending || state.isSessionLoading || state.isImageRefreshLoading) {
    return false
  }

  if (!window.confirm("Soll das aktive Bild wirklich auf das letzte Backup zurückgesetzt werden?")) {
    return false
  }

  appStore.setState({ isImageRefreshLoading: true })
  await waitForNextPaint()

  try {
    const response = await fetch("/api/image/revert-active", { method: "POST" })
    const payload = await readJsonResponse(response)
    if (!response.ok) {
      appStore.setState({ errorMessage: getErrorMessage(payload, "Bild konnte nicht zurückgesetzt werden.") })
      return false
    }

    appStore.setState({ imageUrl: appendCacheBuster("/api/image/current"), errorMessage: "" })
    await pollImageSignature(true)
    return true
  } catch (error) {
    appStore.setState({ errorMessage: error instanceof Error ? error.message : "Bild konnte nicht zurückgesetzt werden." })
    return false
  } finally {
    appStore.setState({ isImageRefreshLoading: false })
  }
}

async function deleteImage() {
  const state = appStore.getState()
  if (state.isSending || state.isSessionLoading || state.isImageRefreshLoading) {
    return false
  }

  if (!window.confirm("Soll das aktuelle Bild wirklich gelöscht werden?")) {
    return false
  }

  appStore.setState({ isImageRefreshLoading: true })
  await waitForNextPaint()

  try {
    const response = await fetch("/api/image/delete-active", { method: "DELETE" })
    const payload = await readJsonResponse(response)
    if (!response.ok) {
      appStore.setState({ errorMessage: getErrorMessage(payload, "Bild konnte nicht gelöscht werden.") })
      return false
    }
    appStore.setState({ ...mapStatePayload(payload), errorMessage: "", isImageExpanded: false })
    return true
  } catch (error) {
    appStore.setState({ errorMessage: error instanceof Error ? error.message : "Bild konnte nicht gelöscht werden." })
    return false
  } finally {
    appStore.setState({ isImageRefreshLoading: false })
  }
}

async function resetNpc() {
  const state = appStore.getState()
  if (state.isSending || state.isSessionLoading) {
    return false
  }

  if (!window.confirm("Soll der Verlauf des aktiven NPC wirklich gelöscht werden?")) {
    return false
  }

  appStore.setState({ isSessionLoading: true })
  try {
    const response = await fetch("/api/npc/reset-active", { method: "DELETE" })
    const payload = await readJsonResponse(response)
    if (!response.ok) {
      appStore.setState({ errorMessage: getErrorMessage(payload, "Verlauf konnte nicht gelöscht werden.") })
      return false
    }
    appStore.setState({ ...mapStatePayload(payload), errorMessage: "" })
    return true
  } catch (error) {
    appStore.setState({ errorMessage: error instanceof Error ? error.message : "Verlauf konnte nicht gelöscht werden." })
    return false
  } finally {
    appStore.setState({ isSessionLoading: false })
  }
}

async function resetNpcAndDynamicScene() {
  const state = appStore.getState()
  if (state.isSending || state.isSessionLoading || !state.isDynamicScene) {
    return false
  }

  if (!window.confirm("Soll der Verlauf und die erstellte Szene wirklich gelöscht werden?")) {
    return false
  }

  appStore.setState({ isSessionLoading: true })
  try {
    const response = await fetch("/api/scene/reset-active", { method: "DELETE" })
    const payload = await readJsonResponse(response)
    if (!response.ok) {
      appStore.setState({ errorMessage: getErrorMessage(payload, "Verlauf und Szene konnten nicht gelöscht werden.") })
      return false
    }
    appStore.setState({ ...mapStatePayload(payload), errorMessage: "" })
    return true
  } catch (error) {
    appStore.setState({ errorMessage: error instanceof Error ? error.message : "Verlauf und Szene konnten nicht gelöscht werden." })
    return false
  } finally {
    appStore.setState({ isSessionLoading: false })
  }
}

function handleChatStreamEvent(event, assistantId, assistantTimestamp) {
  if (!event || typeof event.type !== "string") {
    throw new Error("Ungültige Streaming-Antwort vom Server.")
  }

  if (event.type === "chunk") {
    const delta = typeof event.delta === "string" ? event.delta : ""
    if (!delta) {
      return false
    }

    const state = appStore.getState()
    appStore.setState({
      messages: appendAssistantChunk(state.messages, assistantId, assistantTimestamp, delta),
    })
    return false
  }

  if (event.type === "done") {
    return true
  }

  if (event.type === "error") {
    throw new Error(getErrorMessage(event, "Nachricht konnte nicht gesendet werden."))
  }

  throw new Error("Ungültige Streaming-Antwort vom Server.")
}

async function streamAssistantReply(text, assistantId, assistantTimestamp) {
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
        isDone = handleChatStreamEvent(parseChatStreamEvent(line), assistantId, assistantTimestamp) || isDone
      }
      newlineIndex = buffer.indexOf("\n")
    }

    if (done) {
      break
    }
  }

  const trailingLine = buffer.trim()
  if (trailingLine) {
    isDone = handleChatStreamEvent(parseChatStreamEvent(trailingLine), assistantId, assistantTimestamp) || isDone
  }

  if (!isDone) {
    throw new Error("Nachricht wurde unvollständig übertragen.")
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
  const assistantTimestamp = createNowTimestamp()
  const messages = state.messages.filter((message) => !String(message?.id || "").startsWith("context-"))
  messages.push({ id: `user-${Date.now()}`, role: "user", content: text, timestamp_utc: createNowTimestamp() })
  appStore.setState({
    messages,
    input: "",
    isSending: true,
    isAssistantTyping: true,
  })

  try {
    await streamAssistantReply(text, assistantId, assistantTimestamp)
    appStore.setState({ errorMessage: "" })
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
    appStore.setState({ isSending: false, isAssistantTyping: false })
  }
}

function toggleTheme() {
  const nextTheme = appStore.getState().theme === "dark" ? "light" : "dark"
  localStorage.setItem("theme", nextTheme)
  document.documentElement.setAttribute("data-theme", nextTheme)
  syncThemeChrome(nextTheme)
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

async function toggleImageAutogenerate() {
   const nextValue = !appStore.getState().imageAutogenerate
   try {
     const response = await fetch("/api/session", {
       method: "PUT",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify({ image_autogenerate: nextValue }),
     })
     const payload = await readJsonResponse(response)
     if (!response.ok) {
       appStore.setState({ errorMessage: getErrorMessage(payload, "Einstellung konnte nicht gespeichert werden.") })
       return
     }
     appStore.setState({ ...mapStatePayload(payload), errorMessage: "" })
   } catch (error) {
     appStore.setState({ errorMessage: error instanceof Error ? error.message : "Einstellung konnte nicht gespeichert werden." })
   }
 }

async function createScene(payload = {}) {
  const state = appStore.getState()
  if (state.isSending || state.isSessionLoading || state.isSceneCreatorLoading) {
    return
  }

  const sceneDescription = typeof payload.scene_description === "string" ? payload.scene_description.trim() : ""

  if (!sceneDescription) {
    appStore.setState({ sceneCreatorError: "Szenenbeschreibung ist erforderlich." })
    return
  }

  appStore.setState({ isSceneCreatorLoading: true, sceneCreatorError: "" })
  await waitForNextPaint()

  try {
    const response = await fetch("/api/scenes/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scene_description: sceneDescription,
      }),
    })
    const responsePayload = await readJsonResponse(response)
    if (!response.ok) {
      appStore.setState({ sceneCreatorError: getErrorMessage(responsePayload, "Szene und NPC-Kontext konnten nicht erstellt werden.") })
      return
    }

    appStore.setState({ ...mapStatePayload(responsePayload), errorMessage: "" })
  } catch (error) {
    appStore.setState({
      sceneCreatorError: error instanceof Error ? error.message : "Szene und NPC-Kontext konnten nicht erstellt werden.",
    })
  } finally {
    appStore.setState({ isSceneCreatorLoading: false })
  }
}

 async function updateUserProfile(content = "") {
   const state = appStore.getState()
   if (state.isSending || state.isSessionLoading) {
     return
   }

   try {
     const response = await fetch("/api/user-profile", {
       method: "PUT",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify({ content }),
     })
     const payload = await readJsonResponse(response)
     if (!response.ok) {
       appStore.setState({ errorMessage: getErrorMessage(payload, "User Profile konnte nicht aktualisiert werden.") })
       return
     }
     appStore.setState({ ...mapStatePayload(payload), errorMessage: "" })
   } catch (error) {
     appStore.setState({ errorMessage: error instanceof Error ? error.message : "User Profile konnte nicht aktualisiert werden." })
   }
}

async function loadCheckpoints() {
   const state = appStore.getState()
   if (state.isHistoryLoading) {
     return
   }

   appStore.setState({ isHistoryLoading: true, historyError: "" })
   try {
     const response = await fetch("/api/history/list", { cache: "no-store" })
     const payload = await readJsonResponse(response)
     if (!response.ok) {
       appStore.setState({ historyError: getErrorMessage(payload, "Checkpoints konnten nicht geladen werden.") })
       return
     }

     appStore.setState({ checkpoints: Array.isArray(payload.checkpoints) ? payload.checkpoints : [] })
   } catch (error) {
     appStore.setState({ historyError: error instanceof Error ? error.message : "Checkpoints konnten nicht geladen werden." })
   } finally {
     appStore.setState({ isHistoryLoading: false })
   }
 }

 async function saveCheckpoint() {
   const state = appStore.getState()
   if (state.isSending || state.isSessionLoading || state.isHistoryLoading) {
     return false
   }

   let shouldReloadCheckpoints = false
   appStore.setState({ isHistoryLoading: true, historyError: "" })
   await waitForNextPaint()

   try {
     const response = await fetch("/api/history/save", { method: "POST" })
     const payload = await readJsonResponse(response)
     if (!response.ok) {
       appStore.setState({ historyError: getErrorMessage(payload, "Checkpoint konnte nicht erstellt werden.") })
       return false
     }

     shouldReloadCheckpoints = true
     return true
   } catch (error) {
     appStore.setState({ historyError: error instanceof Error ? error.message : "Checkpoint konnte nicht erstellt werden." })
     return false
   } finally {
     appStore.setState({ isHistoryLoading: false })
     if (shouldReloadCheckpoints) {
       await loadCheckpoints()
     }
   }
 }

 async function restoreCheckpoint(commitHash) {
   const state = appStore.getState()
   if (state.isSending || state.isSessionLoading || !commitHash) {
     return false
   }

   if (!window.confirm("Soll dieser Spielstand wirklich wiederhergestellt werden?")) {
     return false
   }

   appStore.setState({ isSessionLoading: true, historyError: "" })
   await waitForNextPaint()

   try {
     const response = await fetch("/api/history/restore", {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify({ commit_hash: commitHash }),
     })
     const payload = await readJsonResponse(response)
     if (!response.ok) {
       appStore.setState({ historyError: getErrorMessage(payload, "Spielstand konnte nicht wiederhergestellt werden.") })
       return false
     }

     // Neu laden nach erfolgreicher Wiederherstellung
     window.location.reload()
     return true
   } catch (error) {
     appStore.setState({ historyError: error instanceof Error ? error.message : "Spielstand konnte nicht wiederhergestellt werden." })
     return false
   } finally {
     appStore.setState({ isSessionLoading: false })
   }
 }

export const appActions = {
    loadInitialState,
    submitMessage,
    updateSession,
    refreshImage,
    revertImage,
    deleteImage,
    resetNpc,
    resetNpcAndDynamicScene,
    setInput,
    toggleTheme,
    toggleSelectorPanel,
    toggleImageExpand,
    setImageError,
    updateUserProfile,
    toggleImageAutogenerate,
    createScene,
    loadCheckpoints,
    saveCheckpoint,
    restoreCheckpoint,
  }
