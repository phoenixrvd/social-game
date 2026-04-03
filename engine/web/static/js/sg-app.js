import "./sg-chat.js"
import "./sg-input.js"
import "./sg-scene-image.js"
import { trustedHtml } from "./trusted-types.js"


const INITIAL_FIELDS = ["scene", "character", "ltm"]
const GENERIC_INITIAL_ERROR_MESSAGE = "Aktion fehlgeschlagen."

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

function createNowTimestamp() {
  return new Date().toISOString()
}

function appendCacheBuster(url) {
  if (!url) {
    return ""
  }
  const separator = url.includes("?") ? "&" : "?"
  return `${url}${separator}t=${Date.now()}`
}

function parseSseEvent(rawEvent) {
  const dataLines = rawEvent
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trim())

  if (!dataLines.length) {
    return null
  }

  return JSON.parse(dataLines.join("\n"))
}

function nextFrame() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve())
  })
}

function buildContextFallbackMessage(data) {
  const characterDescription =
    typeof data?.character_description === "string" && data.character_description.trim()
      ? data.character_description
      : "Keine Charakterbeschreibung verfuegbar."
  const sceneDescription =
    typeof data?.scene_description === "string" && data.scene_description.trim()
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

class SocialGameApp extends HTMLElement {
  constructor() {
    super()
    this.state = {
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
      npcs: [],
      scenes: [],
      activeAssistantId: "",
      imageSignature: "",
      messagesSignature: "",
      isMobileImageExpanded: false,
      isSelectorPanelOpen: localStorage.getItem("selectorPanelOpen") === "true",
      theme: localStorage.getItem("theme") === "light" ? "light" : "dark",
      initialState: { scene: "", character: "", ltm: "" },
      initialSavedState: { scene: "", character: "", ltm: "" },
      initialEditState: { scene: false, character: false, ltm: false },
      initialStateUnavailable: false,
      initialStateError: "",
      canEditInitialState: false,
    }
    this.sessionHealthTimerId = null
    this.visualViewportUpdateFrameId = null
    this.visualViewportSettleTimerId = null
    this.visualViewportShouldKeepPinnedScroll = false
    this.isScrollPinned = true
    this.pinnedScrollScheduled = false
    this.resizeObserver = null
    this.mutationObserver = null
    this._connected = false
    this._boundHandleScroll = this.handleScroll.bind(this)
    this._boundHandleResize = this.handleResize.bind(this)
    this._boundHandleVisualViewportResize = () => this.scheduleVisualViewportUpdate({ keepPinnedScroll: true })
    this._boundHandleVisualViewportScroll = () => this.scheduleVisualViewportUpdate({ keepPinnedScroll: false })
    this._boundHandleVisibilityChange = this.handleVisibilityChange.bind(this)
    this._boundHandleMessageSubmit = (event) => this.handleSubmit(event.detail?.message)
    this._boundHandleInputChange = (event) => {
      this.state.input = typeof event.detail?.value === "string" ? event.detail.value : ""
    }
    this._boundHandleSessionChange = (event) => this.updateSession(event.detail)
    this._boundHandleSelectorToggle = () => this.toggleSelectorPanel()
    this._boundHandleThemeToggle = () => this.toggleTheme()
    this._boundHandleImageRefresh = () => this.refreshActiveImage()
    this._boundHandleResetActiveNpc = () => this.resetActiveNpcData()
    this._boundHandleInitialDraftChange = (event) => this.handleInitialDraftChange(event.detail)
    this._boundHandleInitialAction = (event) => this.handleInitialAction(event.detail)
    this._boundHandleImageLoad = () => this.setImageLoading(false)
    this._boundHandleImageError = () => this.handleImageError()
    this._boundHandleImageExpandToggle = (event) => this.setMobileImageExpanded(event.detail?.expanded)
  }

  connectedCallback() {
    if (this._connected) {
      return
    }
    this._connected = true
    this.renderShell()
    this.toggleEventHandlers(true)
    document.documentElement.setAttribute("data-theme", this.state.theme)
    this.renderAll()
    this.setupScrollPin()
    syncViewportHeight()
    syncPortraitShellWidth()
    this.syncChatFormOffset()
    this.loadInitialState().finally(() => {
      this.startSessionHealthPolling()
    })
    requestAnimationFrame(() => {
      this.querySelector("sg-input")?.focusInput()
    })
  }

  disconnectedCallback() {
    this.stopSessionHealthPolling()
    if (this.visualViewportUpdateFrameId !== null) {
      cancelAnimationFrame(this.visualViewportUpdateFrameId)
      this.visualViewportUpdateFrameId = null
    }
    if (this.visualViewportSettleTimerId !== null) {
      clearTimeout(this.visualViewportSettleTimerId)
      this.visualViewportSettleTimerId = null
    }
    this.resizeObserver?.disconnect()
    this.mutationObserver?.disconnect()
    this.toggleEventHandlers(false)
    document.body.classList.remove("sg-overflow-y-hidden")
    this._connected = false
  }

  renderShell() {
    this.innerHTML = trustedHtml(`
      <div class="app-viewport">
        <div class="sg-layout-root">
          <div class="sg-chat-pane">
            <sg-chat class="sg-chat-component"></sg-chat>
            <sg-input class="sg-input-component"></sg-input>
          </div>

          <sg-scene-image class="sg-scene-image-slot"></sg-scene-image>
        </div>
      </div>
    `)
  }

  toggleEventHandlers(attach) {
    const method = attach ? "addEventListener" : "removeEventListener"
    this.toggleComponentEventHandlers(method)
    this.toggleWindowEventHandlers(method)
    this.toggleVisualViewportEventHandlers(method)
    this.toggleMessagesScrollHandler(method)
  }

  toggleComponentEventHandlers(method) {
    const listeners = [
      ["sg:message-submit", this._boundHandleMessageSubmit],
      ["sg:input-change", this._boundHandleInputChange],
      ["sg:session-change", this._boundHandleSessionChange],
      ["sg:selector-toggle", this._boundHandleSelectorToggle],
      ["sg:theme-toggle", this._boundHandleThemeToggle],
      ["sg:image-refresh", this._boundHandleImageRefresh],
      ["sg:reset-active-npc", this._boundHandleResetActiveNpc],
      ["sg:initial-draft-change", this._boundHandleInitialDraftChange],
      ["sg:initial-action", this._boundHandleInitialAction],
      ["sg:image-load", this._boundHandleImageLoad],
      ["sg:image-error", this._boundHandleImageError],
      ["sg:image-expand-toggle", this._boundHandleImageExpandToggle],
    ]
    listeners.forEach(([eventName, handler]) => this[method](eventName, handler))
  }

  toggleWindowEventHandlers(method) {
    window[method]("resize", this._boundHandleResize)
    window[method]("scroll", this._boundHandleScroll, { passive: true })
    document[method]("visibilitychange", this._boundHandleVisibilityChange)
  }

  toggleVisualViewportEventHandlers(method) {
    if (!window.visualViewport) {
      return
    }
    window.visualViewport[method]("resize", this._boundHandleVisualViewportResize)
    window.visualViewport[method]("scroll", this._boundHandleVisualViewportScroll)
  }

  toggleMessagesScrollHandler(method) {
    const chat = this.querySelector("sg-chat")
    if (method === "addEventListener") {
      chat?.addMessagesScrollListener(this._boundHandleScroll, { passive: true })
      return
    }

    chat?.removeMessagesScrollListener(this._boundHandleScroll, { passive: true })
  }

  setError(message) {
    this.setState({ errorMessage: typeof message === "string" ? message.trim() : "" })
  }

  clearError() {
    this.setState({ errorMessage: "" })
  }

  toggleTheme() {
    const theme = this.state.theme === "light" ? "dark" : "light"
    localStorage.setItem("theme", theme)
    document.documentElement.setAttribute("data-theme", theme)
    this.setState({ theme })
  }

  toggleSelectorPanel() {
    const isSelectorPanelOpen = !this.state.isSelectorPanelOpen
    localStorage.setItem("selectorPanelOpen", isSelectorPanelOpen ? "true" : "false")
    this.setState({ isSelectorPanelOpen })
  }

  setImageLoading(isLoading) {
    this.state.isImageLoading = Boolean(isLoading)
    this.renderInput()
  }

  setImage(url) {
    if (!url) {
      this.setState({ imageUrl: "", isMobileImageExpanded: false, isImageLoading: false })
      return
    }

    this.setState({ imageUrl: url, isImageLoading: true })
  }

  handleImageError() {
    this.setState({ imageUrl: "", isMobileImageExpanded: false, isImageLoading: false })
  }

  setMobileImageExpanded(nextExpanded) {
    const targetExpanded = isMobileViewport() ? Boolean(nextExpanded) && Boolean(this.state.imageUrl) : false
    if (this.state.isMobileImageExpanded !== targetExpanded) {
      this.setState({ isMobileImageExpanded: targetExpanded })
    }
  }

  renderChat() {
    const messages = this.state.messages.map((message) => this.decorateMessageForInitialState(message))
    this.querySelector("sg-chat")?.setState({
      messages,
      isSending: this.state.isSending,
      activeAssistantId: this.state.activeAssistantId,
    })
    if (this.isScrollPinned) {
      requestAnimationFrame(() => {
        if (this.isScrollPinned) {
          this.scrollMessagesToBottom("instant")
        }
      })
    }
  }

  decorateMessageForInitialState(message) {
    if (!message || typeof message !== "object") {
      return message
    }
    if (message.id === "context-character") {
      return {
        ...message,
        initialField: "character",
        initialValue: this.state.initialState.character,
        initialSavedValue: this.state.initialSavedState.character,
        initialDirty: this.isInitialFieldDirty("character"),
        initialEditing: this.state.initialEditState.character,
        initialEditable: this.state.canEditInitialState && !this.state.initialStateUnavailable,
      }
    }
    if (message.id === "context-scene") {
      return {
        ...message,
        initialField: "scene",
        initialValue: this.state.initialState.scene,
        initialSavedValue: this.state.initialSavedState.scene,
        initialDirty: this.isInitialFieldDirty("scene"),
        initialEditing: this.state.initialEditState.scene,
        initialEditable: this.state.canEditInitialState && !this.state.initialStateUnavailable,
      }
    }
    return message
  }

  renderInput() {
    this.querySelector("sg-input")?.setState({
      input: this.state.input,
      isSending: this.state.isSending,
      isSessionLoading: this.state.isSessionLoading,
      isImageLoading: this.state.isImageLoading,
      isImageRefreshLoading: this.state.isImageRefreshLoading,
      errorMessage: this.state.errorMessage,
      imageUpdateError: this.state.imageUpdateError,
      selectorPanelOpen: this.state.isSelectorPanelOpen,
      theme: this.state.theme,
      npcs: this.state.npcs,
      scenes: this.state.scenes,
      npcId: this.state.npcId,
      sceneId: this.state.sceneId,
      initial: this.state.initialState,
      initialSaved: this.state.initialSavedState,
      initialEdit: this.state.initialEditState,
      initialUnavailable: this.state.initialStateUnavailable,
      initialErrorMessage: this.state.initialStateError,
      canEditInitial: this.state.canEditInitialState,
    })
    this.syncChatFormOffset()
  }

  renderImage() {
    this.querySelector("sg-scene-image")?.setState({
      imageUrl: this.state.imageUrl,
      isExpanded: this.state.isMobileImageExpanded && isMobileViewport(),
    })
    document.body.classList.toggle("sg-overflow-y-hidden", this.state.isMobileImageExpanded && isMobileViewport())
  }

  renderAll() {
    this.renderChat()
    this.renderInput()
    this.renderImage()
  }

  setState(patch = {}) {
    Object.assign(this.state, patch)
    this.renderAll()
  }

  syncChatFormOffset() {
    if (!isMobileViewport()) {
      document.documentElement.style.setProperty("--chat-form-offset", "1rem")
      return
    }

    const formHeight = this.querySelector("sg-input")?.measureFormHeight()
    if (!formHeight) {
      return
    }

    const minimumMobileOffset = 88
    const extraSpacing = 8
    const nextOffset = Math.max(minimumMobileOffset, Math.ceil(formHeight + extraSpacing))
    document.documentElement.style.setProperty("--chat-form-offset", `${nextOffset}px`)
  }

  getLastVisibleMessageId() {
    for (let index = this.state.messages.length - 1; index >= 0; index -= 1) {
      const message = this.state.messages[index]
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

  isNearBottom() {
    if (isMobileViewport()) {
      const fallbackOffset = 88
      const bottomThreshold = 8
      const offset = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--chat-form-offset")) || fallbackOffset
      return window.innerHeight + window.scrollY >= document.body.scrollHeight - offset - bottomThreshold
    }

    return this.querySelector("sg-chat")?.isMessagesNearBottom(8) ?? true
  }

  scrollMessagesToBottom(behavior = "smooth") {
    if (isMobileViewport()) {
      window.scrollTo({ top: document.body.scrollHeight, behavior })
      return
    }

    this.querySelector("sg-chat")?.scrollMessagesToBottom(behavior)
  }

  pinScrollToBottom() {
    this.isScrollPinned = true
    this.scrollMessagesToBottom("instant")
  }

  schedulePinnedScroll() {
    if (this.pinnedScrollScheduled) {
      return
    }

    this.pinnedScrollScheduled = true
    requestAnimationFrame(() => {
      this.pinnedScrollScheduled = false
      if (this.isScrollPinned && !this.isInitialEditorFocused()) {
        this.scrollMessagesToBottom("instant")
      }
    })
  }

  isInitialEditorFocused() {
    const activeElement = document.activeElement
    if (!(activeElement instanceof HTMLTextAreaElement)) {
      return false
    }

    return activeElement.classList.contains("sg-initial-context-textarea") || activeElement.classList.contains("sg-initial-textarea")
  }

  handleScroll() {
    this.isScrollPinned = this.isNearBottom()
  }

  setupScrollPin() {
    const chat = this.querySelector("sg-chat")
    this.resizeObserver = chat?.observeMessagesResize(() => {
      this.schedulePinnedScroll()
    })

    this.mutationObserver = chat?.observeMessagesMutations(() => {
      this.schedulePinnedScroll()
    })
  }

  applyVisualViewportUpdate({ keepPinnedScroll = false } = {}) {
    syncViewportHeight()
    syncPortraitShellWidth()
    this.syncChatFormOffset()

    if (keepPinnedScroll && this.isScrollPinned) {
      this.scrollMessagesToBottom("instant")
    }
  }

  scheduleVisualViewportUpdate({ keepPinnedScroll = false } = {}) {
    if (!isMobileViewport()) {
      this.applyVisualViewportUpdate({ keepPinnedScroll })
      return
    }

    this.visualViewportShouldKeepPinnedScroll = this.visualViewportShouldKeepPinnedScroll || keepPinnedScroll

    if (this.visualViewportUpdateFrameId === null) {
      this.visualViewportUpdateFrameId = requestAnimationFrame(() => {
        const nextKeepPinnedScroll = this.visualViewportShouldKeepPinnedScroll
        this.visualViewportUpdateFrameId = null
        this.visualViewportShouldKeepPinnedScroll = false
        this.applyVisualViewportUpdate({ keepPinnedScroll: nextKeepPinnedScroll })
      })
    }

    if (this.visualViewportSettleTimerId !== null) {
      clearTimeout(this.visualViewportSettleTimerId)
    }

    const viewportSettleDelayMs = 48
    this.visualViewportSettleTimerId = setTimeout(() => {
      const nextKeepPinnedScroll = this.visualViewportShouldKeepPinnedScroll || keepPinnedScroll
      this.visualViewportSettleTimerId = null
      this.visualViewportShouldKeepPinnedScroll = false
      this.applyVisualViewportUpdate({ keepPinnedScroll: nextKeepPinnedScroll })
    }, viewportSettleDelayMs)
  }

  updateImageErrorFromPayload(data) {
    this.state.imageUpdateError = typeof data?.image_update_error === "string" ? data.image_update_error.trim() : ""
  }

  applyState(data) {
    this.state.messages = ensureContextMessage(data.messages, data)
    this.updateImageErrorFromPayload(data)
    this.state.messagesSignature = typeof data.messages_signature === "string" ? data.messages_signature : ""
    this.state.imageSignature = typeof data.image_signature === "string" ? data.image_signature : ""
    this.state.npcName = data.npc_name || "NPC"
    this.state.npcId = data.npc_id || ""
    this.state.sceneId = data.scene_id || ""
    this.state.npcs = Array.isArray(data.npcs) ? data.npcs : []
    this.state.scenes = Array.isArray(data.scenes) ? data.scenes : []

    if (data.image_url) {
      this.setImage(appendCacheBuster(data.image_url))
    } else {
      this.setImage("")
    }
  }

  createEmptyInitialEditState() {
    return { scene: false, character: false, ltm: false }
  }

  resetInitialState() {
    this.state.initialState = { scene: "", character: "", ltm: "" }
    this.state.initialSavedState = { scene: "", character: "", ltm: "" }
    this.state.initialEditState = this.createEmptyInitialEditState()
    this.state.initialStateUnavailable = false
    this.state.initialStateError = ""
    this.state.canEditInitialState = false
  }

  applyInitialState(data) {
    this.state.initialState = {
      scene: typeof data?.scene_description === "string" ? data.scene_description : "",
      character: typeof data?.character_description === "string" ? data.character_description : "",
      ltm: typeof data?.ltm === "string" ? data.ltm : "",
    }
    this.state.initialSavedState = { ...this.state.initialState }
    this.state.canEditInitialState = Boolean(data?.editable)
    this.state.initialStateUnavailable = false
    this.state.initialStateError = ""
    if (!this.state.canEditInitialState) {
      this.state.initialEditState = this.createEmptyInitialEditState()
    }
  }

  handleInitialDraftChange(detail = {}) {
    const field = typeof detail.field === "string" ? detail.field : ""
    if (!INITIAL_FIELDS.includes(field)) {
      return
    }
    this.state.initialState[field] = typeof detail.value === "string" ? detail.value : ""

    if (field === "ltm") {
      this.renderInput()
    }
  }

  isInitialFieldDirty(field) {
    return this.state.initialState[field] !== this.state.initialSavedState[field]
  }

  async loadInitialEditorState({ isFirstLoad = false } = {}) {
    try {
      const response = await fetch("/api/initial-state", { cache: "no-store" })
      const data = await response.json()
      if (!response.ok) {
        const patch = { initialStateError: GENERIC_INITIAL_ERROR_MESSAGE }
        if (isFirstLoad) {
          Object.assign(patch, { initialStateUnavailable: true, canEditInitialState: false, initialEditState: this.createEmptyInitialEditState() })
        }
        this.setState(patch)
        return
      }
      this.applyInitialState(data)
    } catch (_error) {
      this.state.initialStateError = GENERIC_INITIAL_ERROR_MESSAGE
      if (isFirstLoad) {
        this.state.initialStateUnavailable = true
        this.state.canEditInitialState = false
        this.state.initialEditState = this.createEmptyInitialEditState()
      }
    }
    this.renderAll()
  }

  async saveInitialField(field) {
    try {
      const response = await fetch(`/api/initial-state/${encodeURIComponent(field)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value: this.state.initialState[field] }),
      })
      const data = await response.json()
      if (!response.ok) {
        this.setState({ initialStateError: GENERIC_INITIAL_ERROR_MESSAGE })
        return
      }
      this.applyInitialState(data)
      this.state.initialEditState[field] = false
      if (field !== "ltm") {
        await this.loadInitialState()
        return
      }
    } catch (_error) {
      this.state.initialStateError = GENERIC_INITIAL_ERROR_MESSAGE
    }
    this.renderAll()
  }

  async revertInitialField(field) {
    const hasUnsavedChanges = this.isInitialFieldDirty(field)
    if (hasUnsavedChanges) {
      const shouldRevert = window.confirm("Ungespeicherte Aenderungen verwerfen und auf Initialstand zuruecksetzen?")
      if (!shouldRevert) {
        return
      }
    }
    try {
      const response = await fetch(`/api/initial-state/${encodeURIComponent(field)}/revert`, {
        method: "POST",
      })
      const data = await response.json()
      if (!response.ok) {
        this.setState({ initialStateError: GENERIC_INITIAL_ERROR_MESSAGE })
        return
      }
      this.applyInitialState(data)
      if (field !== "ltm") {
        await this.loadInitialState()
        return
      }
    } catch (_error) {
      this.state.initialStateError = GENERIC_INITIAL_ERROR_MESSAGE
    }
    this.renderAll()
  }

  async handleInitialAction(detail = {}) {
    const action = typeof detail.action === "string" ? detail.action : ""
    const field = typeof detail.field === "string" ? detail.field : ""
    if (!INITIAL_FIELDS.includes(field)) {
      return
    }
    if (this.state.isSending || this.state.isSessionLoading || this.state.initialStateUnavailable) {
      return
    }

    if (action === "initial-toggle-edit") {
      this.setState({
        initialEditState: { ...this.state.initialEditState, [field]: !this.state.initialEditState[field] },
        initialStateError: "",
      })
      return
    }

    if (action === "initial-save") {
      await this.saveInitialField(field)
      return
    }

    if (action === "initial-revert") {
      await this.revertInitialField(field)
    }
  }

  async renderMessagesGradually(messages) {
    if (!isMobileViewport()) {
      this.state.messages = [...messages]
      this.renderChat()
      await nextFrame()
      this.pinScrollToBottom()
      return
    }

    this.state.messages = []
    this.pinScrollToBottom()
    this.renderChat()

    for (let index = messages.length - 1; index >= 0; index -= 1) {
      this.state.messages.unshift(messages[index])
      this.renderChat()
      await nextFrame()
    }

    await nextFrame()
    this.pinScrollToBottom()
  }

  async streamAssistantReply(text, assistantMessage) {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    })

    if (!response.ok) {
      const data = await response.json()
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
      buffer = this.consumeSseBuffer(buffer, assistantMessage)
    }
  }

  consumeSseBuffer(buffer, assistantMessage) {
    const events = buffer.split("\n\n")
    const rest = events.pop() || ""
    for (const rawEvent of events) {
      const payload = parseSseEvent(rawEvent)
      if (!payload) {
        continue
      }
      this.applyStreamPayload(payload, assistantMessage)
    }
    return rest
  }

  applyStreamPayload(payload, assistantMessage) {
    if (payload.type === "error") {
      throw new Error(payload.detail || "Nachricht konnte nicht gesendet werden.")
    }

    if (payload.type === "chunk" && typeof payload.text === "string") {
      assistantMessage.content += payload.text
      this.renderChat()
      return
    }

    if (payload.type === "done") {
      this.applyDonePayload(payload, assistantMessage)
    }
  }

  applyDonePayload(payload, assistantMessage) {
    if (payload.assistant_message) {
      assistantMessage.id = payload.assistant_message.id || assistantMessage.id
      assistantMessage.content = payload.assistant_message.content || assistantMessage.content
      assistantMessage.timestamp = payload.assistant_message.timestamp || assistantMessage.timestamp
    }
    if (payload.image_url) {
      this.setImage(appendCacheBuster(payload.image_url))
    }
  }

  async syncSignaturesFromHealth() {
    try {
      const response = await fetch("/health", { cache: "no-store" })
      if (!response.ok) {
        console.warn(`Health-Check /health lieferte Status ${response.status}.`)
        return
      }

      const data = await response.json()
      if (data.messages_signature) {
        this.state.messagesSignature = data.messages_signature
      }
      if (data.image_signature) {
        this.state.imageSignature = data.image_signature
      }
      this.updateImageErrorFromPayload(data)
      this.renderInput()
    } catch (error) {
      console.error("Health-Signaturen konnten nicht synchronisiert werden.", error)
    }
  }

  async loadInitialState() {
    this.clearError()

    try {
      const response = await fetch("/api/state")
      const data = await response.json()

      if (!response.ok) {
        this.setImage("")
        this.setError(data.detail || "State konnte nicht geladen werden.")
        this.resetInitialState()
        this.renderAll()
        return
      }

      const loadedMessages = ensureContextMessage(data.messages, data)
      this.applyState({ ...data, messages: [] })
      this.renderAll()
      await this.renderMessagesGradually(loadedMessages)
      await this.loadInitialEditorState({ isFirstLoad: true })
    } catch (error) {
      this.setImage("")
      this.setError(error instanceof Error ? error.message : "Backend nicht erreichbar.")
      this.resetInitialState()
    }

    this.renderAll()
    this.pinScrollToBottom()
  }

  async loadOnlyMissingMessages(targetSignature) {
    const afterId = this.getLastVisibleMessageId()
    const suffix = afterId ? `?after_id=${encodeURIComponent(afterId)}` : ""
    const response = await fetch(`/api/messages/delta${suffix}`, { cache: "no-store" })
    const data = await response.json()

    if (!response.ok) {
      await this.loadInitialState()
      return
    }

    if (data.reset_required) {
      this.state.messagesSignature = ""
      await this.loadInitialState()
      return
    }

    const incoming = Array.isArray(data.messages) ? data.messages : []
    this.mergeIncomingMessages(incoming)

    this.state.messagesSignature =
      typeof data.messages_signature === "string" && data.messages_signature ? data.messages_signature : targetSignature
  }

  mergeIncomingMessages(incoming) {
    if (incoming.length === 0) {
      return
    }

    const knownIds = new Set(
      this.state.messages
        .filter((message) => message && typeof message.id === "string")
        .map((message) => message.id)
    )
    const freshMessages = incoming.filter((message) => message && typeof message.id === "string" && !knownIds.has(message.id))
    if (freshMessages.length === 0) {
      return
    }

    const hasVisibleConversation = this.state.messages.some(
      (message) => message && typeof message.id === "string" && !message.id.startsWith("context-")
    )
    this.state.messages = hasVisibleConversation ? [...this.state.messages, ...freshMessages] : freshMessages
    this.renderChat()
    this.pinScrollToBottom()
  }

  async checkSessionHealth() {
    if (this.state.isSending || this.state.isSessionLoading) {
      return
    }

    try {
      const response = await fetch("/health", { cache: "no-store" })
      if (!response.ok) {
        return
      }

      const data = await response.json()
      if (!data.npc_id && !data.scene_id) {
        return
      }

      if (this.hasSessionChanged(data)) {
        this.state.messagesSignature = ""
        this.state.imageSignature = ""
        await this.loadInitialState()
        return
      }

      if (await this.syncMessagesFromHealth(data)) {
        return
      }

      this.syncImageFromHealth(data)
      this.syncImageErrorFromHealth(data)
    } catch (error) {
      this.stopSessionHealthPolling()
      this.setError(error instanceof Error ? error.message : "Health-Check fehlgeschlagen.")
    }
  }

  hasSessionChanged(data) {
    return (data.npc_id && data.npc_id !== this.state.npcId) || (data.scene_id && data.scene_id !== this.state.sceneId)
  }

  async syncMessagesFromHealth(data) {
    if (!data.messages_signature) {
      return false
    }
    if (!this.state.messagesSignature) {
      this.state.messagesSignature = data.messages_signature
      return false
    }
    if (data.messages_signature === this.state.messagesSignature) {
      return false
    }

    await this.loadOnlyMissingMessages(data.messages_signature)
    return true
  }

  syncImageFromHealth(data) {
    if (!data.image_signature) {
      return
    }
    if (!this.state.imageSignature) {
      this.state.imageSignature = data.image_signature
      return
    }
    if (data.image_signature === this.state.imageSignature) {
      return
    }

    this.state.imageSignature = data.image_signature
    this.setImage(appendCacheBuster("/api/image/current"))
  }

  syncImageErrorFromHealth(data) {
    if (typeof data.image_update_error !== "string") {
      return
    }
    const nextError = data.image_update_error.trim()
    if (nextError !== this.state.imageUpdateError) {
      this.setState({ imageUpdateError: nextError })
    }
  }

  startSessionHealthPolling() {
    if (this.sessionHealthTimerId !== null) {
      return
    }
    const healthPollingIntervalMs = 4000
    this.sessionHealthTimerId = setInterval(() => {
      this.checkSessionHealth()
    }, healthPollingIntervalMs)
  }

  stopSessionHealthPolling() {
    if (this.sessionHealthTimerId !== null) {
      clearInterval(this.sessionHealthTimerId)
      this.sessionHealthTimerId = null
    }
  }

  async updateSession(nextSession = {}) {
    this.state.isSessionLoading = true
    this.clearError()
    this.renderAll()

    try {
      const response = await fetch("/api/session", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(nextSession),
      })

      const data = await response.json()
      if (!response.ok) {
        this.setError(data.detail || "Session konnte nicht aktualisiert werden.")
        await this.loadInitialState()
      } else {
        const loadedMessages = ensureContextMessage(data.messages, data)
        this.applyState({ ...data, messages: [] })
        this.renderAll()
        await this.renderMessagesGradually(loadedMessages)
        await this.loadInitialEditorState({ isFirstLoad: true })
      }
    } catch (error) {
      this.setError(error instanceof Error ? error.message : "Session konnte nicht aktualisiert werden.")
      await this.loadInitialState()
    } finally {
      this.state.isSessionLoading = false
      this.renderAll()
    }
  }

  async resetActiveNpcData() {
    const npcLabel = this.state.npcName || this.state.npcId || "den aktiven NPC"
    const shouldDelete = window.confirm(`Soll der Verlauf fuer ${npcLabel} wirklich geloescht werden?`)
    if (!shouldDelete || this.state.isSending || this.state.isSessionLoading) {
      return
    }

    this.state.isSessionLoading = true
    this.clearError()
    this.renderAll()

    try {
      const response = await fetch("/api/npc/reset-active", {
        method: "DELETE",
      })
      const data = await response.json()

      if (!response.ok) {
        this.setError(data.detail || "NPC-Daten konnten nicht geloescht werden.")
        return
      }

      this.state.imageSignature = ""
      await this.loadInitialState()
    } catch (error) {
      this.setError(error instanceof Error ? error.message : "NPC-Daten konnten nicht geloescht werden.")
    } finally {
      this.state.isSessionLoading = false
      this.renderAll()
    }
  }

  async refreshActiveImage() {
    if (this.state.isSending || this.state.isSessionLoading) {
      return
    }

    this.state.isSessionLoading = true
    this.state.isImageRefreshLoading = true
    this.clearError()
    this.renderAll()

    try {
      const response = await fetch("/api/image/refresh-active", {
        method: "POST",
      })
      const data = await response.json()

      this.updateImageErrorFromPayload(data)
      this.renderInput()

      if (!response.ok) {
        this.setError(data.detail || "Bild konnte nicht aktualisiert werden.")
        return
      }

      this.state.imageSignature = ""
      this.setImage(appendCacheBuster("/api/image/current"))
      await this.syncSignaturesFromHealth()
    } catch (error) {
      this.setError(error instanceof Error ? error.message : "Bild konnte nicht aktualisiert werden.")
    } finally {
      this.state.isImageRefreshLoading = false
      this.state.isSessionLoading = false
      this.renderAll()
    }
  }

  async handleSubmit(submittedText) {
    const text = typeof submittedText === "string" ? submittedText.trim() : this.state.input.trim()
    if (!text || this.state.isSending || this.state.isSessionLoading) {
      return
    }

    this.clearError()
    this.state.messages.push({
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
    this.state.messages.push(assistantMessage)
    this.setState({
      activeAssistantId: assistantMessage.id,
      input: "",
      isSending: true,
      canEditInitialState: false,
      initialEditState: this.createEmptyInitialEditState(),
    })
    this.pinScrollToBottom()

    try {
      await this.streamAssistantReply(text, assistantMessage)
    } catch (error) {
      this.state.messages = this.state.messages.filter((message) => message !== assistantMessage)
      this.setError(error instanceof Error ? error.message : "Nachricht konnte nicht gesendet werden.")
    } finally {
      this.setState({ isSending: false, activeAssistantId: "" })
    }
  }

  handleResize() {
    syncViewportHeight()
    syncPortraitShellWidth()
    this.syncChatFormOffset()
    if (!isMobileViewport() && this.state.isMobileImageExpanded) {
      this.setState({ isMobileImageExpanded: false })
      return
    }
    this.renderImage()
    if (this.isScrollPinned) {
      requestAnimationFrame(() => {
        if (this.isScrollPinned) {
          this.scrollMessagesToBottom("instant")
        }
      })
    }
  }

  handleVisibilityChange() {
    if (document.hidden) {
      this.stopSessionHealthPolling()
      return
    }

    this.checkSessionHealth()
    this.startSessionHealthPolling()
  }

}

function runSelfTests() {
  console.assert(appendCacheBuster("/image.png").startsWith("/image.png?t="), "appendCacheBuster should append query to plain URL")
  console.assert(appendCacheBuster("/image.png?a=1").includes("&t="), "appendCacheBuster should append query to URL with existing params")
  console.assert(typeof createNowTimestamp() === "string", "createNowTimestamp should return a string")
  console.assert(parseSseEvent('data: {"type":"chunk"}\n\n')?.type === "chunk", "parseSseEvent should parse valid payloads")
}

customElements.get("sg-app") || customElements.define("sg-app", SocialGameApp)

runSelfTests()

