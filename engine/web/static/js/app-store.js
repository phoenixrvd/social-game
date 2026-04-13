function createInitialState() {
  return {
    messages: [],
    input: "",
    imageUrl: null,
    imageSignature: null,
    errorMessage: null,
    isSending: false,
    isAssistantTyping: false,
    isSessionLoading: false,
    isImageRefreshLoading: false,
    activeAssistantId: null,
    npcs: [],
    scenes: [],
    npcId: null,
    sceneId: null,
    isImageExpanded: false,
    isSelectorPanelOpen: false,
    focusRequestedAt: null,
    theme: localStorage.getItem("theme") === "light" ? "light" : "dark",
  }
}

class AppStore {
  constructor() {
    this._state = createInitialState()
    this._listeners = new Map()
  }

  getState() {
    return this._state
  }

  subscribe(key, listener) {
    if (typeof key !== "string" || !key || typeof listener !== "function") {
      return () => {}
    }

    const listeners = this._listeners.get(key) || new Set()
    listeners.add(listener)
    this._listeners.set(key, listeners)

    return () => {
      listeners.delete(listener)
      if (listeners.size === 0) {
        this._listeners.delete(key)
      }
    }
  }

  setState(patch = {}) {
    const prevState = this._state
    const nextState = { ...prevState, ...(patch || {}) }

    this._state = nextState

    for (const key of Object.keys(patch || {})) {
      if (prevState[key] === nextState[key]) {
        continue
      }

      const listeners = this._listeners.get(key)
      if (listeners) {
        for (const listener of listeners) {
          listener(nextState[key], prevState[key], nextState)
        }
      }
    }
  }
}

export const appStore = new AppStore()
