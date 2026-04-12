import "./sg-chat.js"
import "./sg-input.js"
import "./sg-scene-image.js"


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

function isMobileViewport() {
  return window.matchMedia("(max-width: 1023px)").matches
}

async function readJsonResponse(response) {
  return response.json().catch(() => ({}))
}

function getErrorMessage(payload, fallbackMessage) {
  return typeof payload?.detail === "string" && payload.detail.trim() ? payload.detail.trim() : fallbackMessage
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
    requestAnimationFrame(() => resolve())
  })
}

class SocialGameApp extends HTMLElement {
  constructor() {
    super()
    this.state = {
      messages: [],
      input: "",
      imageUrl: "",
      errorMessage: "",
      isSending: false,
      isSessionLoading: false,
      isImageRefreshLoading: false,
      activeAssistantId: "",
      npcs: [],
      scenes: [],
      npcId: "",
      sceneId: "",
      isImageExpanded: false,
      isSelectorPanelOpen: false,
      theme: localStorage.getItem("theme") === "light" ? "light" : "dark",
    }

    this.$ = {}
    this._imageSignature = ""
    this._imagePollTimer = null
  }

  connectedCallback() {
    document.documentElement.setAttribute("data-theme", this.state.theme)
    this.innerHTML = `
      <div class="app-viewport">
        <div class="sg-layout-root">
          <section class="sg-chat-pane" aria-label="Dialogbereich">
            <sg-chat class="sg-chat-component"></sg-chat>
            <sg-input class="sg-input-component"></sg-input>
          </section>

          <section class="sg-scene-image-slot" aria-label="Szenenbild">
            <sg-scene-image></sg-scene-image>
          </section>
        </div>
      </div>
    `

    this.$ = {
      chat: this.querySelector("sg-chat"),
      input: this.querySelector("sg-input"),
      image: this.querySelector("sg-scene-image"),
    }

    const listeners = [
      ["sg:input-change", this.handleInputChange.bind(this)],
      ["sg:message-submit", this.handleSubmit.bind(this)],
      ["sg:session-change", this.updateSession.bind(this)],
      ["sg:image-refresh", this.refreshActiveImage.bind(this)],
      ["sg:reset-active-npc", this.resetActiveNpcData.bind(this)],
      ["sg:selector-toggle", this.toggleSelectorPanel.bind(this)],
      ["sg:theme-toggle", this.toggleTheme.bind(this)],
      ["sg:image-error", this.handleImageError.bind(this)],
      ["sg:image-expand-toggle", this.handleImageExpandToggle.bind(this)],
    ]
    listeners.forEach(([name, handler]) => this.addEventListener(name, handler))

    this.renderAll()
    this.loadInitialState()
  }

  setState(patch = {}) {
    Object.assign(this.state, patch)
    this.renderAll()
  }

  setInputState(patch = {}) {
    Object.assign(this.state, patch)
    this.renderInput()
  }

  setError(message) {
    this.setState({errorMessage: typeof message === "string" ? message.trim() : ""})
  }

  clearError() {
    this.setState({errorMessage: ""})
  }

  toggleSelectorPanel() {
    this.setState({isSelectorPanelOpen: !this.state.isSelectorPanelOpen})
  }

  toggleTheme() {
    const nextTheme = this.state.theme === "dark" ? "light" : "dark"
    localStorage.setItem("theme", nextTheme)
    document.documentElement.setAttribute("data-theme", nextTheme)
    this.setState({theme: nextTheme})
  }

  handleInputChange(event) {
    this.state.input = typeof event.detail?.value === "string" ? event.detail.value : ""
  }

  handleImageExpandToggle(event) {
    this.state.isImageExpanded = Boolean(event.detail?.expanded)
    document.body.classList.toggle("sg-overflow-y-hidden", this.state.isImageExpanded && isMobileViewport())
  }

  applyStatePayload(payload = {}) {
    this.state.messages = Array.isArray(payload.messages) ? payload.messages : []
    this.state.imageUrl = payload.image_url ? appendCacheBuster(payload.image_url) : ""
    this._imageSignature = typeof payload.image_signature === "string" ? payload.image_signature : ""
    this.state.npcs = Array.isArray(payload.npcs) ? payload.npcs : []
    this.state.scenes = Array.isArray(payload.scenes) ? payload.scenes : []
    this.state.npcId = typeof payload.npc_id === "string" ? payload.npc_id : ""
    this.state.sceneId = typeof payload.scene_id === "string" ? payload.scene_id : ""
  }

  renderChat() {
    this.$.chat?.setState({
      messages: this.state.messages,
      isSending: this.state.isSending,
      activeAssistantId: this.state.activeAssistantId,
    })
  }

  renderInput() {
    this.$.input?.setState({
      input: this.state.input,
      isSending: this.state.isSending,
      isSessionLoading: this.state.isSessionLoading,
      isImageRefreshLoading: this.state.isImageRefreshLoading,
      errorMessage: this.state.errorMessage,
      selectorPanelOpen: this.state.isSelectorPanelOpen,
      theme: this.state.theme,
      npcs: this.state.npcs,
      scenes: this.state.scenes,
      npcId: this.state.npcId,
      sceneId: this.state.sceneId,
    })
  }

  renderImage() {
    this.$.image?.setState({
      imageUrl: this.state.imageUrl,
      isExpanded: this.state.isImageExpanded,
      isLoading: this.state.isImageRefreshLoading,
    })
  }

  renderAll() {
    this.renderChat()
    this.renderInput()
    this.renderImage()
  }

  startImagePolling(intervalMs = 5000) {
    this.stopImagePolling()
    this._imagePollTimer = setInterval(() => this.pollImageSignature(), intervalMs)
  }

  stopImagePolling() {
    if (this._imagePollTimer !== null) {
      clearInterval(this._imagePollTimer)
      this._imagePollTimer = null
    }
  }

  async pollImageSignature() {
    if (this.state.isSending || this.state.isSessionLoading || this.state.isImageRefreshLoading) {
      return
    }
    try {
      const response = await fetch("/api/image/signature", {cache: "no-store"})
      if (!response.ok) {
        return
      }
      const payload = await response.json()
      const newSignature = typeof payload.signature === "string" ? payload.signature : ""
      if (!newSignature || newSignature === this._imageSignature) {
        return
      }
      this._imageSignature = newSignature
      const rawUrl = typeof payload.image_url === "string" ? payload.image_url : ""
      this.state.imageUrl = rawUrl ? appendCacheBuster(rawUrl) : ""
      this.renderImage()
    } catch {
      // Netzwerkfehler beim Polling werden still ignoriert
    }
  }

  async loadInitialState() {
    this.setState({isSessionLoading: true})
    try {
      const response = await fetch("/api/state", {cache: "no-store"})
      const payload = await readJsonResponse(response)
      if (!response.ok) {
        this.setError(getErrorMessage(payload, "State konnte nicht geladen werden."))
        return
      }
      this.applyStatePayload(payload)
      this.renderAll()
    } catch (error) {
      this.setError(error instanceof Error ? error.message : "Backend nicht erreichbar.")
    } finally {
      this.setState({isSessionLoading: false})
      requestAnimationFrame(() => this.$.input?.focusInput())
      this.startImagePolling()
    }
  }

  async updateSession(nextSession = {}) {
    if (nextSession instanceof Event) {
      nextSession = nextSession.detail
    }

    if (this.state.isSending) {
      return
    }

    this.setState({isSessionLoading: true, errorMessage: ""})
    try {
      const response = await fetch("/api/session", {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(nextSession),
      })
      const payload = await readJsonResponse(response)
      if (!response.ok) {
        this.setError(getErrorMessage(payload, "Session konnte nicht aktualisiert werden."))
        return
      }
      this.applyStatePayload(payload)
      this.renderAll()
    } catch (error) {
      this.setError(error instanceof Error ? error.message : "Session konnte nicht aktualisiert werden.")
    } finally {
      this.setState({isSessionLoading: false})
    }
  }

  handleImageError() {
    this.setState({imageUrl: "", isImageExpanded: false})
  }

  async refreshActiveImage() {
    if (this.state.isSending || this.state.isSessionLoading) {
      return
    }

    this.setInputState({isImageRefreshLoading: true, errorMessage: ""})
    this.renderImage()
    await waitForNextPaint()
    try {
      const response = await fetch("/api/image/refresh-active", {method: "POST"})
      const payload = await readJsonResponse(response)

      if (!response.ok) {
        this.setInputState({
          errorMessage: getErrorMessage(payload, "Bild konnte nicht aktualisiert werden."),
        })
        return
      }

      const newUrl = appendCacheBuster("/api/image/current")
      this.setInputState({imageUrl: newUrl})
      this.renderImage()

      // Signatur neu holen damit das Polling nicht erneut triggert
      try {
        const sigResponse = await fetch("/api/image/signature", {cache: "no-store"})
        if (sigResponse.ok) {
          const sigPayload = await sigResponse.json()
          this._imageSignature = typeof sigPayload.signature === "string" ? sigPayload.signature : this._imageSignature
        }
      } catch (error) {
        // Der Bild-Refresh ist bereits erfolgreich; Signaturfehler nur diagnostisch protokollieren.
        console.warn("Signatur-Refresh nach Bildaktualisierung fehlgeschlagen.", error)
      }
    } catch (error) {
      this.setInputState({errorMessage: error instanceof Error ? error.message : "Bild konnte nicht aktualisiert werden."})
    } finally {
      this.setInputState({isImageRefreshLoading: false})
      this.renderImage()
    }
  }

  async resetActiveNpcData() {
    if (this.state.isSending || this.state.isSessionLoading) {
      return
    }

    const shouldDelete = window.confirm("Soll der Verlauf des aktiven NPC wirklich gelöscht werden?")
    if (!shouldDelete) {
      return
    }

    this.setState({isSessionLoading: true, errorMessage: ""})
    try {
      const response = await fetch("/api/npc/reset-active", {method: "DELETE"})
      const payload = await readJsonResponse(response)
      if (!response.ok) {
        this.setError(getErrorMessage(payload, "Verlauf konnte nicht gelöscht werden."))
        return
      }
      this.applyStatePayload(payload)
      this.renderAll()
    } catch (error) {
      this.setError(error instanceof Error ? error.message : "Verlauf konnte nicht gelöscht werden.")
    } finally {
      this.setState({isSessionLoading: false})
    }
  }

  handleChatStreamEvent(event, assistantMessage) {
    if (!event || typeof event.type !== "string") {
      throw new Error("Ungültige Streaming-Antwort vom Server.")
    }

    if (event.type === "chunk") {
      const delta = typeof event.delta === "string" ? event.delta : ""
      assistantMessage.content += delta
      this.renderChat()
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

  async streamAssistantReply(text, assistantMessage) {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text}),
    })

    if (!response.ok || !response.body) {
      const payload = await readJsonResponse(response)
      throw new Error(getErrorMessage(payload, "Nachricht konnte nicht gesendet werden."))
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder("utf-8")
    let buffer = ""
    let isDone = false

    while (true) {
      const {done, value} = await reader.read()
      buffer += decoder.decode(value || new Uint8Array(), {stream: !done})

      let newlineIndex = buffer.indexOf("\n")
      while (newlineIndex !== -1) {
        const line = buffer.slice(0, newlineIndex).trim()
        buffer = buffer.slice(newlineIndex + 1)
        if (line) {
          isDone = this.handleChatStreamEvent(parseChatStreamEvent(line), assistantMessage) || isDone
        }
        newlineIndex = buffer.indexOf("\n")
      }

      if (done) {
        break
      }
    }

    const trailingLine = buffer.trim()
    if (trailingLine) {
      isDone = this.handleChatStreamEvent(parseChatStreamEvent(trailingLine), assistantMessage) || isDone
    }

    if (!isDone) {
      throw new Error("Nachricht wurde unvollständig übertragen.")
    }
  }

  async handleSubmit(submittedText) {
    if (submittedText instanceof Event) {
      submittedText = submittedText.detail?.message
    }

    const text = typeof submittedText === "string" ? submittedText.trim() : this.state.input.trim()
    if (!text || this.state.isSending || this.state.isSessionLoading) {
      return
    }

    this.state.messages = this.state.messages.filter((message) => !String(message?.id || "").startsWith("context-"))
    this.clearError()

    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: createNowTimestamp(),
    }
    const assistantMessage = {
      id: `assistant-local-${Date.now()}`,
      role: "assistant",
      content: "",
      timestamp: createNowTimestamp(),
    }

    this.state.messages.push(userMessage, assistantMessage)
    this.setState({input: "", isSending: true, activeAssistantId: assistantMessage.id})

    try {
      await this.streamAssistantReply(text, assistantMessage)
    } catch (error) {
      if (!assistantMessage.content.trim()) {
        this.state.messages = this.state.messages.filter((message) => message !== assistantMessage)
      }
      this.setError(error instanceof Error ? error.message : "Nachricht konnte nicht gesendet werden.")
    } finally {
      this.setState({isSending: false, activeAssistantId: ""})
    }
  }
}

customElements.get("sg-app") || customElements.define("sg-app", SocialGameApp)
