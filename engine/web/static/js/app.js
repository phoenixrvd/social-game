const state = {
  messages: [],
  input: "",
  imageUrl: "",
  isSending: false,
  isImageLoading: false,
  isSessionLoading: false,
  isImageRefreshLoading: false,
  errorMessage: "",
  imageUpdateError: "",
  npcName: "NPC",
  npcId: "",
  sceneId: "",
  characterDescription: "",
  sceneDescription: "",
  characterData: {},
  npcs: [],
  scenes: [],
  statusText: "Bereit.",
  activeAssistantId: "",
  imageSignature: "",
  messagesSignature: "",
  isMobileImageExpanded: false,
  isSelectorPanelOpen: localStorage.getItem("selectorPanelOpen") === "true",
  theme: localStorage.getItem("theme") === "light" ? "light" : "dark",
}

const elements = {
  layoutRoot: document.getElementById("layout-root"),
  chatPane: document.getElementById("chat-pane"),
  npcSelect: document.getElementById("npc-select"),
  sceneSelect: document.getElementById("scene-select"),
  composerHint: document.getElementById("composer-hint"),
  selectorPanel: document.getElementById("selector-panel"),
  selectorToggleButton: document.getElementById("selector-toggle-button"),
  themeToggleButton: document.getElementById("theme-toggle-button"),
  imageRefreshButton: document.getElementById("image-refresh-button"),
  deleteButton: document.getElementById("delete-button"),
  messages: document.getElementById("messages"),
  form: document.getElementById("chat-form"),
  input: document.getElementById("chat-input"),
  sendButton: document.getElementById("send-button"),
  imageSpinner: document.getElementById("image-spinner"),
  imageMain: document.getElementById("image-main"),
  imageBg: document.getElementById("image-bg"),
  imageFrame: document.getElementById("image-frame"),
  imageEmpty: document.getElementById("image-empty"),
  imagePane: document.getElementById("image-pane"),
  imageContent: document.getElementById("image-content"),
  imageOverlay: document.getElementById("image-overlay"),
  imageOverlayBg: document.getElementById("image-overlay-bg"),
  imageOverlayMain: document.getElementById("image-overlay-main"),
}

function isMobileViewport() {
  return window.matchMedia("(max-width: 1023px)").matches
}

function syncViewportHeight() {
  const viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight
  document.documentElement.style.setProperty("--app-vh", `${Math.round(viewportHeight)}px`)
}

function syncPortraitShellWidth() {
  const screenWidth = typeof window.screen?.width === "number" ? window.screen.width : window.innerWidth
  const screenHeight = typeof window.screen?.height === "number" ? window.screen.height : window.innerHeight
  const shortSide = Math.min(screenWidth, screenHeight)
  const fallbackWidth = Math.min(window.innerWidth, shortSide)
  document.documentElement.style.setProperty("--portrait-shell-width", `${Math.round(fallbackWidth)}px`)
}

function syncChatFormOffset() {
  if (!isMobileViewport()) {
    document.documentElement.style.setProperty("--chat-form-offset", "1rem")
    return
  }

  const formRect = elements.form.getBoundingClientRect()
  const nextOffset = Math.max(88, Math.ceil(formRect.height + 8))
  document.documentElement.style.setProperty("--chat-form-offset", `${nextOffset}px`)
}

function applyMobileImageLayout() {
  const expanded = state.isMobileImageExpanded && isMobileViewport()

  // Basisansicht bleibt stabil; Expanded wird als echtes Overlay gerendert.
  elements.imageMain.classList.add("object-contain")
  elements.imageMain.classList.remove("object-cover")
  elements.imageMain.classList.add("w-auto", "max-w-full")
  elements.imageMain.classList.remove("w-full")

  elements.imageOverlay.classList.toggle("is-open", expanded)
  document.body.classList.toggle("overflow-y-hidden", expanded)
}

function setMobileImageExpanded(nextExpanded) {
  if (!isMobileViewport()) {
    state.isMobileImageExpanded = false
    applyMobileImageLayout()
    return
  }

  const targetExpanded = Boolean(nextExpanded) && Boolean(state.imageUrl)
  if (state.isMobileImageExpanded === targetExpanded) {
    return
  }

  state.isMobileImageExpanded = targetExpanded
  applyMobileImageLayout()
}

function formatTimestamp(timestamp) {
  if (!timestamp) return ""

  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return timestamp

  return new Intl.DateTimeFormat("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

function createNowTimestamp() {
  return new Date().toISOString()
}

function appendCacheBuster(url) {
  if (!url) return ""
  const separator = url.includes("?") ? "&" : "?"
  return `${url}${separator}t=${Date.now()}`
}

function buildApiUrl(path) {
  return path
}

async function parseJsonSafely(response) {
  try {
    return await response.json()
  } catch {
    return {}
  }
}

function parseSseEvent(rawEvent) {
  const dataLines = rawEvent
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trim())

  if (!dataLines.length) {
    return null
  }

  try {
    return JSON.parse(dataLines.join("\n"))
  } catch {
    return null
  }
}

async function streamAssistantReply(text, assistantMessage) {
  const response = await fetch(buildApiUrl("/api/chat/stream"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  })

  if (!response.ok) {
    const data = await parseJsonSafely(response)
    throw new Error(data.detail || "Nachricht konnte nicht gesendet werden.")
  }

  if (!response.body) {
    throw new Error("Streaming wird vom Browser nicht unterstuetzt.")
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split("\n\n")
    buffer = events.pop() || ""

    events.forEach((rawEvent) => {
      const payload = parseSseEvent(rawEvent)
      if (!payload) {
        return
      }

      if (payload.type === "chunk" && typeof payload.text === "string") {
        assistantMessage.content += payload.text
        renderMessages()
        return
      }

      if (payload.type === "error") {
        throw new Error(payload.detail || "Nachricht konnte nicht gesendet werden.")
      }

      if (payload.type === "done") {
        if (payload.assistant_message) {
          assistantMessage.id = payload.assistant_message.id || assistantMessage.id
          assistantMessage.content = payload.assistant_message.content || assistantMessage.content
          assistantMessage.timestamp = payload.assistant_message.timestamp || assistantMessage.timestamp
        }
        if (payload.image_url) {
          setImage(appendCacheBuster(buildApiUrl(payload.image_url)))
        }
      }
    })
  }
}

function autoResizeTextarea() {
  elements.input.style.height = "0px"
  elements.input.style.height = `${Math.min(elements.input.scrollHeight, 220)}px`
  syncChatFormOffset()
}

function setStatus(text) {
  state.statusText = text
}

function updateImageErrorFromPayload(data) {
  state.imageUpdateError = typeof data?.image_update_error === "string" ? data.image_update_error.trim() : ""
}

function renderComposerHint() {
  const error = state.errorMessage || state.imageUpdateError
  if (error) {
    elements.composerHint.textContent = error
    elements.composerHint.classList.add("text-red-300")
    elements.composerHint.classList.remove("hidden")
    return
  }

  elements.composerHint.textContent = "Enter = senden, Shift+Enter = neue Zeile"
  elements.composerHint.classList.remove("text-red-300")
  elements.composerHint.classList.add("hidden")
}

function setError(message) {
  state.errorMessage = typeof message === "string" ? message.trim() : ""
  renderComposerHint()
}

function clearError() {
  state.errorMessage = ""
  renderComposerHint()
}

function renderSelectorPanel() {
  const open = state.isSelectorPanelOpen
  elements.selectorPanel.classList.toggle("hidden", !open)
  elements.selectorToggleButton.className = open
    ? "icon-button icon-button-active rounded-lg p-1.5 transition"
    : "icon-button rounded-lg p-1.5 transition"
  elements.selectorToggleButton.setAttribute("aria-pressed", open ? "true" : "false")
  syncChatFormOffset()
}

function getThemeToggleIcon(theme) {
  if (theme === "dark") {
    return `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4" aria-hidden="true">
        <circle cx="12" cy="12" r="4"></circle>
        <path d="M12 2v2"></path>
        <path d="M12 20v2"></path>
        <path d="M4.93 4.93l1.41 1.41"></path>
        <path d="M17.66 17.66l1.41 1.41"></path>
        <path d="M2 12h2"></path>
        <path d="M20 12h2"></path>
        <path d="M6.34 17.66l-1.41 1.41"></path>
        <path d="M19.07 4.93l-1.41 1.41"></path>
      </svg>
    `
  }

  return `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4" aria-hidden="true">
      <path d="M21 12.79A9 9 0 1 1 11.21 3c0 0 0 0 0 0a7 7 0 0 0 9.79 9.79z"></path>
    </svg>
  `
}

function applyTheme() {
  document.documentElement.setAttribute("data-theme", state.theme)
}

function renderThemeToggle() {
  const isDark = state.theme === "dark"
  elements.themeToggleButton.innerHTML = getThemeToggleIcon(state.theme)
  elements.themeToggleButton.setAttribute("aria-pressed", isDark ? "true" : "false")
  elements.themeToggleButton.setAttribute("title", isDark ? "Helles Theme aktivieren" : "Dunkles Theme aktivieren")
  elements.themeToggleButton.setAttribute("aria-label", isDark ? "Helles Theme aktivieren" : "Dunkles Theme aktivieren")
}

function toggleTheme() {
  state.theme = state.theme === "light" ? "dark" : "light"
  localStorage.setItem("theme", state.theme)
  applyTheme()
  renderThemeToggle()
}

function toggleSelectorPanel() {
  state.isSelectorPanelOpen = !state.isSelectorPanelOpen
  localStorage.setItem("selectorPanelOpen", state.isSelectorPanelOpen ? "true" : "false")
  renderSelectorPanel()
}

function setImageLoading(isLoading) {
  state.isImageLoading = isLoading
  elements.imageSpinner.classList.toggle("hidden", !isLoading)
}

function setImage(url) {
  if (!url) {
    state.imageUrl = ""
    setMobileImageExpanded(false)
    elements.imageFrame.classList.add("hidden")
    elements.imageEmpty.classList.remove("hidden")
    setImageLoading(false)
    return
  }

  state.imageUrl = url
  applyMobileImageLayout()
  elements.imageFrame.classList.remove("hidden")
  elements.imageEmpty.classList.add("hidden")
  setImageLoading(true)
  elements.imageBg.src = url
  elements.imageMain.src = url
  elements.imageOverlayBg.src = url
  elements.imageOverlayMain.src = url
}

let sessionHealthTimerId = null
let visualViewportUpdateFrameId = null
let visualViewportSettleTimerId = null
let visualViewportShouldKeepPinnedScroll = false

function applyVisualViewportUpdate({ keepPinnedScroll = false } = {}) {
  syncViewportHeight()
  syncPortraitShellWidth()
  syncChatFormOffset()

  if (keepPinnedScroll && isScrollPinned) {
    scrollMessagesToBottom("instant")
  }
}

function scheduleVisualViewportUpdate({ keepPinnedScroll = false } = {}) {
  if (!isMobileViewport()) {
    applyVisualViewportUpdate({ keepPinnedScroll })
    return
  }

  visualViewportShouldKeepPinnedScroll = visualViewportShouldKeepPinnedScroll || keepPinnedScroll

  if (visualViewportUpdateFrameId === null) {
    visualViewportUpdateFrameId = requestAnimationFrame(() => {
      const nextKeepPinnedScroll = visualViewportShouldKeepPinnedScroll
      visualViewportUpdateFrameId = null
      visualViewportShouldKeepPinnedScroll = false
      applyVisualViewportUpdate({ keepPinnedScroll: nextKeepPinnedScroll })
    })
  }

  if (visualViewportSettleTimerId !== null) {
    clearTimeout(visualViewportSettleTimerId)
  }

  visualViewportSettleTimerId = setTimeout(() => {
    const nextKeepPinnedScroll = visualViewportShouldKeepPinnedScroll || keepPinnedScroll
    visualViewportSettleTimerId = null
    visualViewportShouldKeepPinnedScroll = false
    applyVisualViewportUpdate({ keepPinnedScroll: nextKeepPinnedScroll })
  }, 48)
}

function getLastVisibleMessageId() {
  for (let index = state.messages.length - 1; index >= 0; index -= 1) {
    const message = state.messages[index]
    if (!message || typeof message.id !== "string") {
      continue
    }
    if (message.id.startsWith("context-")) {
      continue
    }
    if (message.role === "user" || message.role === "assistant") {
      return message.id
    }
  }
  return ""
}

async function loadOnlyMissingMessages(targetSignature) {
  const afterId = getLastVisibleMessageId()
  const suffix = afterId ? `?after_id=${encodeURIComponent(afterId)}` : ""
  const response = await fetch(buildApiUrl(`/api/messages/delta${suffix}`), { cache: "no-store" })
  const data = await parseJsonSafely(response)

  if (!response.ok) {
    await loadInitialState()
    return
  }

  if (data.reset_required) {
    state.messagesSignature = ""
    await loadInitialState()
    return
  }

  const incoming = Array.isArray(data.messages) ? data.messages : []
  if (incoming.length > 0) {
    const knownIds = new Set(
      state.messages
        .filter((message) => message && typeof message.id === "string")
        .map((message) => message.id)
    )
    const freshMessages = incoming.filter((message) => message && typeof message.id === "string" && !knownIds.has(message.id))

    if (freshMessages.length > 0) {
      const hasVisibleConversation = state.messages.some(
        (message) => message && typeof message.id === "string" && !message.id.startsWith("context-")
      )
      state.messages = hasVisibleConversation ? [...state.messages, ...freshMessages] : freshMessages
      renderMessages()
      pinScrollToBottom()
    }
  }

  state.messagesSignature =
    typeof data.messages_signature === "string" && data.messages_signature
      ? data.messages_signature
      : targetSignature
}

async function checkSessionHealth() {
  if (state.isSending || state.isSessionLoading) {
    return
  }

  try {
    const response = await fetch(buildApiUrl("/health"), { cache: "no-store" })
    if (!response.ok) {
      return
    }

    const data = await parseJsonSafely(response)
    if (!data.npc_id && !data.scene_id) {
      return
    }

    const sessionChanged =
      (data.npc_id && data.npc_id !== state.npcId) ||
      (data.scene_id && data.scene_id !== state.sceneId)

    if (sessionChanged) {
      state.messagesSignature = ""
      state.imageSignature = ""
      await loadInitialState()
      return
    }

    // Nachrichten-Signatur pruefen - z. B. durch Hintergrundprozesse geaendert
    if (data.messages_signature) {
      if (!state.messagesSignature) {
        state.messagesSignature = data.messages_signature
      } else if (data.messages_signature !== state.messagesSignature) {
        await loadOnlyMissingMessages(data.messages_signature)
        return
      }
    }

    // Bild-Signatur pruefen
    if (data.image_signature) {
      if (!state.imageSignature) {
        state.imageSignature = data.image_signature
      } else if (data.image_signature !== state.imageSignature) {
        state.imageSignature = data.image_signature
        setImage(appendCacheBuster(buildApiUrl("/api/image/current")))
      }
    }

    if (typeof data.image_update_error === "string") {
      const nextError = data.image_update_error.trim()
      if (nextError !== state.imageUpdateError) {
        state.imageUpdateError = nextError
        renderComposerHint()
      }
    }
  } catch {
    // Health-Check-Fehler still behandeln.
  }
}

function startSessionHealthPolling() {
  if (sessionHealthTimerId !== null) {
    return
  }
  sessionHealthTimerId = setInterval(checkSessionHealth, 4000)
}

function stopSessionHealthPolling() {
  if (sessionHealthTimerId !== null) {
    clearInterval(sessionHealthTimerId)
    sessionHealthTimerId = null
  }
}

function renderSelectOptions(selectElement, options, value) {
  selectElement.innerHTML = ""

  options.forEach((option) => {
    const element = document.createElement("option")
    element.value = option.id
    element.textContent = option.label
    if (option.id === value) {
      element.selected = true
    }
    selectElement.appendChild(element)
  })
}

let isScrollPinned = true

function isNearBottom() {
  if (isMobileViewport()) {
    const offset = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--chat-form-offset")) || 88
    return window.innerHeight + window.scrollY >= document.body.scrollHeight - offset - 8
  }

  const el = elements.messages
  return el.scrollHeight - el.scrollTop - el.clientHeight <= 8
}

function scrollMessagesToBottom(behavior = "smooth") {
  if (isMobileViewport()) {
    window.scrollTo({ top: document.body.scrollHeight, behavior })
    return
  }

  elements.messages.scrollTo({ top: elements.messages.scrollHeight, behavior })
}

function pinScrollToBottom() {
  isScrollPinned = true
  scrollMessagesToBottom("instant")
}

function setupScrollPin() {
  const onScroll = () => {
    isScrollPinned = isNearBottom()
  }
  elements.messages.addEventListener("scroll", onScroll, { passive: true })
  window.addEventListener("scroll", onScroll, { passive: true })

  let pinnedScrollScheduled = false
  const schedulePinnedScroll = () => {
    if (pinnedScrollScheduled) {
      return
    }

    pinnedScrollScheduled = true
    requestAnimationFrame(() => {
      pinnedScrollScheduled = false
      if (isScrollPinned) {
        scrollMessagesToBottom("instant")
      }
    })
  }

  const resizeObserver = new ResizeObserver(() => {
    schedulePinnedScroll()
  })
  resizeObserver.observe(elements.messages)

  // Bei DOM-Mutationen (neue Chunks/Nachrichten) den Pin-Scroll einplanen.
  const mutationObserver = new MutationObserver(() => {
    schedulePinnedScroll()
  })
  mutationObserver.observe(elements.messages, {
    childList: true,
    subtree: true,
    characterData: true,
  })
}

function nextFrame() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve())
  })
}

async function renderMessagesGradually(messages) {
  if (!isMobileViewport()) {
    state.messages = [...messages]
    renderMessages()
    await nextFrame()
    pinScrollToBottom()
    return
  }

  state.messages = []
  pinScrollToBottom()
  render()

  for (let index = messages.length - 1; index >= 0; index -= 1) {
    state.messages.unshift(messages[index])
    renderMessages()
    await nextFrame()
  }

  await nextFrame()
  pinScrollToBottom()
}

function renderMessages() {
  elements.messages.innerHTML = ""

  state.messages.forEach((message) => {
    const isContextInitial = message.id === "context-character" || message.id === "context-scene"
    const wrapper = document.createElement("div")
    wrapper.className = [
      isContextInitial
        ? "context-rich msg-context w-full max-w-full rounded-2xl px-3 py-2 shadow-sm transition-colors duration-150"
        : "w-fit max-w-[90%] rounded-2xl px-4 py-3 shadow-sm transition-colors duration-150",
      message.role === "user" && !isContextInitial
        ? "ml-auto msg-user"
        : isContextInitial
          ? ""
          : "msg-assistant",
    ].join(" ")

    const content = document.createElement("div")
    content.className = isContextInitial ? "" : "whitespace-pre-wrap"

    const showTypingDots =
      message.role === "assistant" &&
      message.id === state.activeAssistantId &&
      (!message.content || !message.content.trim())

    if (showTypingDots) {
      const dots = document.createElement("div")
      dots.className = "typing-dots"
      dots.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>'
      content.appendChild(dots)
    } else if (typeof message.html === "string" && message.html.trim()) {
      content.innerHTML = message.html
    } else {
      content.textContent = message.content
    }
    wrapper.appendChild(content)

    const formattedTimestamp = formatTimestamp(message.timestamp)
    if (formattedTimestamp) {
      const timestamp = document.createElement("div")
      timestamp.className = [
        "mt-2 flex text-[11px]",
        message.role === "user" ? "justify-end msg-time-user" : "justify-start msg-time-assistant",
      ].join(" ")
      timestamp.textContent = formattedTimestamp
      wrapper.appendChild(timestamp)
    }

    elements.messages.appendChild(wrapper)
  })

  if (state.isSending && !state.activeAssistantId) {
    const loading = document.createElement("div")
    loading.className = "msg-loading w-fit max-w-[90%] rounded-2xl px-4 py-3 shadow-sm"
    loading.textContent = "Antwort wird erzeugt..."
    elements.messages.appendChild(loading)
  }
}

function render() {
  elements.sendButton.disabled = state.isSending || state.isSessionLoading
  elements.imageRefreshButton.disabled = state.isSending || state.isSessionLoading
  elements.imageRefreshButton.classList.toggle("is-refreshing", state.isImageRefreshLoading)
  elements.imageRefreshButton.setAttribute("aria-busy", state.isImageRefreshLoading ? "true" : "false")
  elements.deleteButton.disabled = state.isSending || state.isSessionLoading
  elements.npcSelect.disabled = state.isSending || state.isSessionLoading
  elements.sceneSelect.disabled = state.isSending || state.isSessionLoading
  elements.input.disabled = state.isSessionLoading
  elements.input.value = state.input
  renderComposerHint()
  renderSelectorPanel()
  renderThemeToggle()
  renderSelectOptions(elements.npcSelect, state.npcs, state.npcId)
  renderSelectOptions(elements.sceneSelect, state.scenes, state.sceneId)
  renderMessages()
  autoResizeTextarea()
  syncChatFormOffset()
  if (isScrollPinned) {
    requestAnimationFrame(() => {
      if (isScrollPinned) {
        scrollMessagesToBottom("instant")
      }
    })
  }
}

function buildContextFallbackMessage(data) {
  const characterDescription =
    typeof (data && data.character_description) === "string" && data.character_description.trim()
      ? data.character_description
      : "Keine Charakterbeschreibung verfuegbar."
  const sceneDescription =
    typeof (data && data.scene_description) === "string" && data.scene_description.trim()
      ? data.scene_description
      : "Keine Szenenbeschreibung verfuegbar."

  return [
    {
      id: "context-character",
      role: "assistant",
      content: characterDescription,
      timestamp: "",
    },
    {
      id: "context-scene",
      role: "assistant",
      content: sceneDescription,
      timestamp: "",
    },
  ]
}

function ensureContextMessage(messages, data) {
  if (Array.isArray(messages) && messages.length > 0) {
    return messages
  }
  return buildContextFallbackMessage(data)
}

function applyState(data) {
  state.messages = ensureContextMessage(data.messages, data)
  updateImageErrorFromPayload(data)
  state.npcName = data.npc_name || "NPC"
  state.npcId = data.npc_id || ""
  state.sceneId = data.scene_id || ""
  state.characterDescription = data.character_description || ""
  state.sceneDescription = data.scene_description || ""
  state.characterData = data.character_data && typeof data.character_data === "object" ? data.character_data : {}
  state.npcs = Array.isArray(data.npcs) ? data.npcs : []
  state.scenes = Array.isArray(data.scenes) ? data.scenes : []

  if (data.image_url) {
    setImage(appendCacheBuster(buildApiUrl(data.image_url)))
  } else {
    setImage("")
  }
}

async function syncSignaturesFromHealth() {
  try {
    const response = await fetch(buildApiUrl("/health"), { cache: "no-store" })
    if (!response.ok) return
    const data = await parseJsonSafely(response)
    if (data.messages_signature) state.messagesSignature = data.messages_signature
    if (data.image_signature) state.imageSignature = data.image_signature
    updateImageErrorFromPayload(data)
    renderComposerHint()
  } catch {
    // still behandeln
  }
}

async function loadInitialState() {
  setStatus("Lade Zustand...")
  clearError()

  try {
    const response = await fetch(buildApiUrl("/api/state"))
    const data = await parseJsonSafely(response)

    if (!response.ok) {
      setImage("")
      setError(data.detail || "State konnte nicht geladen werden.")
      render()
      return
    }

    const loadedMessages = ensureContextMessage(data.messages, data)
    applyState({ ...data, messages: [] })
    render()
    await renderMessagesGradually(loadedMessages)
    setStatus("Bereit.")
  } catch {
    setImage("")
    setError("Backend nicht erreichbar.")
  }

  render()
  pinScrollToBottom()
  await syncSignaturesFromHealth()
}

async function updateSession(nextSession) {
  state.isSessionLoading = true
  clearError()
  setStatus("Session wird aktualisiert...")
  render()

  try {
    const response = await fetch(buildApiUrl("/api/session"), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(nextSession),
    })

    const data = await parseJsonSafely(response)
    if (!response.ok) {
      setError(data.detail || "Session konnte nicht aktualisiert werden.")
      await loadInitialState()
    } else {
      const loadedMessages = ensureContextMessage(data.messages, data)
      applyState({ ...data, messages: [] })
      render()
      await renderMessagesGradually(loadedMessages)
      setStatus("Session aktualisiert.")
    }
  } catch (error) {
    setError(error instanceof Error ? error.message : "Session konnte nicht aktualisiert werden.")
    await loadInitialState()
  } finally {
    state.isSessionLoading = false
    render()
  }
}

async function resetActiveNpcData() {
  const npcLabel = state.npcName || state.npcId || "den aktiven NPC"
  const shouldDelete = window.confirm(`Soll der Verlauf fuer ${npcLabel} wirklich geloescht werden?`)
  if (!shouldDelete || state.isSending || state.isSessionLoading) {
    return
  }

  state.isSessionLoading = true
  clearError()
  setStatus("NPC-Daten werden geloescht...")
  render()

  try {
    const response = await fetch(buildApiUrl("/api/npc/reset-active"), {
      method: "DELETE",
    })
    const data = await parseJsonSafely(response)

    if (!response.ok) {
      setError(data.detail || "NPC-Daten konnten nicht geloescht werden.")
      return
    }

    state.imageSignature = ""
    await loadInitialState()
    setStatus("NPC-Daten geloescht.")
  } catch (error) {
    setError(error instanceof Error ? error.message : "NPC-Daten konnten nicht geloescht werden.")
  } finally {
    state.isSessionLoading = false
    render()
  }
}

async function refreshActiveImage() {
  if (state.isSending || state.isSessionLoading) {
    return
  }

  state.isSessionLoading = true
  state.isImageRefreshLoading = true
  clearError()
  setStatus("Bild wird aktualisiert...")
  render()

  try {
    const response = await fetch(buildApiUrl("/api/image/refresh-active"), {
      method: "POST",
    })
    const data = await parseJsonSafely(response)

    updateImageErrorFromPayload(data)
    renderComposerHint()

    if (!response.ok) {
      setError(data.detail || "Bild konnte nicht aktualisiert werden.")
      return
    }

    state.imageSignature = ""
    setImage(appendCacheBuster(buildApiUrl("/api/image/current")))
    await syncSignaturesFromHealth()
    setStatus("Bild aktualisiert.")
  } catch (error) {
    setError(error instanceof Error ? error.message : "Bild konnte nicht aktualisiert werden.")
  } finally {
    state.isImageRefreshLoading = false
    state.isSessionLoading = false
    render()
  }
}

async function handleSubmit(event) {
  if (event) {
    event.preventDefault()
  }

  const text = state.input.trim()
  if (!text || state.isSending || state.isSessionLoading) {
    return
  }

  clearError()
  state.messages.push({
    role: "user",
    content: text,
    timestamp: createNowTimestamp(),
  })
  const assistantMessage = {
    id: `local-${Date.now()}`,
    role: "assistant",
    content: "",
    timestamp: createNowTimestamp(),
  }
  state.messages.push(assistantMessage)
  state.activeAssistantId = assistantMessage.id
  state.input = ""
  state.isSending = true
  setStatus("Nachricht wird gesendet...")
  render()
  pinScrollToBottom()

  try {
    await streamAssistantReply(text, assistantMessage)
  } catch (error) {
    state.messages = state.messages.filter((m) => m !== assistantMessage)
    setError(error instanceof Error ? error.message : "Nachricht konnte nicht gesendet werden.")
    setStatus("Senden fehlgeschlagen.")
  } finally {
    state.isSending = false
    state.activeAssistantId = ""
    render()
  }
}

elements.form.addEventListener("submit", handleSubmit)

elements.selectorToggleButton.addEventListener("click", () => {
  toggleSelectorPanel()
})

elements.themeToggleButton.addEventListener("click", () => {
  toggleTheme()
})

elements.imageRefreshButton.addEventListener("click", () => {
  refreshActiveImage()
})

elements.deleteButton.addEventListener("click", () => {
  resetActiveNpcData()
})

elements.npcSelect.addEventListener("change", (event) => {
  updateSession({ npc_id: event.target.value, scene_id: state.sceneId })
})

elements.sceneSelect.addEventListener("change", (event) => {
  updateSession({ npc_id: state.npcId, scene_id: event.target.value })
})

elements.input.addEventListener("input", (event) => {
  state.input = event.target.value
  autoResizeTextarea()
})

elements.input.addEventListener("focus", () => {
  if (!isMobileViewport()) {
    return
  }

  // Auf Mobile beim Fokus den Chat-Container unten halten (lokaler Scroll statt Window-Scroll).
  requestAnimationFrame(() => {
    if (isScrollPinned) {
      scrollMessagesToBottom("instant")
    }
  })
})

elements.input.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") {
    return
  }

  if (event.shiftKey) {
    event.preventDefault()

    const start = elements.input.selectionStart
    const end = elements.input.selectionEnd
    const nextValue = `${state.input.slice(0, start)}\n${state.input.slice(end)}`

    state.input = nextValue
    elements.input.value = nextValue
    autoResizeTextarea()

    requestAnimationFrame(() => {
      elements.input.selectionStart = start + 1
      elements.input.selectionEnd = start + 1
    })
    return
  }

  event.preventDefault()
  handleSubmit()
})

elements.imageMain.addEventListener("load", () => {
  setImageLoading(false)
})

elements.imageMain.addEventListener("error", () => {
  setImageLoading(false)
  setMobileImageExpanded(false)
  elements.imageFrame.classList.add("hidden")
  elements.imageEmpty.classList.remove("hidden")
})

elements.imageMain.addEventListener("click", (event) => {
  event.stopPropagation()
  if (!state.imageUrl || !isMobileViewport()) {
    return
  }
  setMobileImageExpanded(!state.isMobileImageExpanded)
})

document.addEventListener("click", () => {
  if (!state.isMobileImageExpanded || !isMobileViewport()) {
    return
  }

  setMobileImageExpanded(false)
})

elements.imageOverlay.addEventListener("click", () => {
  if (!state.isMobileImageExpanded) {
    return
  }
  setMobileImageExpanded(false)
})

window.addEventListener("resize", () => {
  syncViewportHeight()
  syncPortraitShellWidth()
  syncChatFormOffset()
  if (isScrollPinned) {
    requestAnimationFrame(() => {
      if (isScrollPinned) {
        scrollMessagesToBottom("instant")
      }
    })
  }
  if (!isMobileViewport() && state.isMobileImageExpanded) {
    setMobileImageExpanded(false)
    return
  }
  applyMobileImageLayout()
})

if (window.visualViewport) {
  window.visualViewport.addEventListener("resize", () => {
    scheduleVisualViewportUpdate({ keepPinnedScroll: true })
  })
  window.visualViewport.addEventListener("scroll", () => {
    scheduleVisualViewportUpdate({ keepPinnedScroll: false })
  })
}

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopSessionHealthPolling()
    return
  }

  checkSessionHealth()
  startSessionHealthPolling()
})

function runSelfTests() {
  console.assert(formatTimestamp(undefined) === "", "formatTimestamp should return empty string for missing timestamp")
  console.assert(formatTimestamp("invalid-date") === "invalid-date", "formatTimestamp should return original value for invalid timestamp")
  console.assert(appendCacheBuster("/image.png").startsWith("/image.png?t="), "appendCacheBuster should append query to plain URL")
  console.assert(appendCacheBuster("/image.png?a=1").includes("&t="), "appendCacheBuster should append query to URL with existing params")
  console.assert(buildApiUrl("/api/state") === "/api/state", "buildApiUrl should keep relative paths")
  console.assert(typeof createNowTimestamp() === "string", "createNowTimestamp should return a string")
}

function focusChatInputOnLoad() {
  requestAnimationFrame(() => {
    if (elements.input.disabled) {
      return
    }
    elements.input.focus()
    const length = elements.input.value.length
    elements.input.setSelectionRange(length, length)
  })
}

try {
  runSelfTests()
} catch {
  // ignore self-test errors in restricted runtimes
}

syncViewportHeight()
syncPortraitShellWidth()
syncChatFormOffset()
applyTheme()
setupScrollPin()
render()
applyMobileImageLayout()
loadInitialState()
startSessionHealthPolling()
focusChatInputOnLoad()

