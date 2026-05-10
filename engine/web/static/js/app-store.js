function createInitialState() {
  return {
    messages: [],
    input: "",
    imageUrl: null,
    imageOriginalUrl: null,
    imageBackups: [],
    imageSignature: null,
    errorMessage: null,
    isSending: false,
    isAssistantTyping: false,
    isSessionLoading: false,
    isImageRefreshLoading: false,
    npcs: [],
    scenes: [],
    npcId: null,
    sceneId: null,
    defaultNpcId: null,
    defaultSceneId: null,
    isDynamicNpc: false,
    isDynamicScene: false,
    isImageExpanded: false,
    isSelectorPanelOpen: false,
    isSceneCreatorLoading: false,
    sceneCreatorError: "",
    isNpcCreatorLoading: false,
    npcCreatorError: "",
    checkpoints: [],
    isHistoryLoading: false,
    historyError: "",
    focusRequestedAt: null,
    theme: localStorage.getItem("theme") === "light" ? "light" : "dark",
    imageAutogenerate: true,
    userProfile: "",
    videoUrl: null,
    imageIsOriginal: true,
    imageVideoAutoplayRequestedAt: null,
  }
}

class AppStore {
  constructor() {
    this._state = createInitialState()
    this._listeners = new Map()
    this._stateListeners = new Set()
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

  subscribeState(listener) {
    if (typeof listener !== "function") {
      return () => {}
    }

    this._stateListeners.add(listener)

    return () => {
      this._stateListeners.delete(listener)
    }
  }

  setState(patch = {}) {
    const prevState = this._state
    const nextState = { ...prevState, ...(patch || {}) }
    const changedKeys = Object.keys(patch || {}).filter((key) => prevState[key] !== nextState[key])

    this._state = nextState

    for (const key of changedKeys) {
      const listeners = this._listeners.get(key)
      if (listeners) {
        for (const listener of listeners) {
          listener(nextState[key], prevState[key], nextState)
        }
      }
    }

    if (changedKeys.length === 0) {
      return
    }

    for (const listener of this._stateListeners) {
      listener(nextState, prevState, changedKeys)
    }
  }
}

export const appStore = new AppStore()
