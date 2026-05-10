import { appStore } from "./app-store.js"
import "./sg-input-context.js"
import "./sg-input-image.js"
import "./sg-input-general.js"
import "./sg-input-scene.js"
import "./sg-input-npc.js"
import "./sg-input-composer.js"
import "./sg-input-history.js"

const SCENE_CREATOR_OPTION_ID = "scene-creator"
const NPC_CREATOR_OPTION_ID = "npc-creator"

function renderTab(optionId, title, isSelected = false, ariaLabel = "") {
  const selected = isSelected ? "true" : "false"
  const tabIndex = isSelected ? "0" : "-1"
  const ariaLabelAttr = ariaLabel ? `aria-label="${ariaLabel}"` : ""
  return /*html*/ `
    <button
      type="button"
      class="sg-options-tab"
      role="tab"
      id="sg-options-tab-${optionId}"
      data-option="${optionId}"
      aria-selected="${selected}"
      aria-controls="sg-options-tab-panel-${optionId}"
      tabindex="${tabIndex}"
      ${ariaLabelAttr}
    >
      ${title}
    </button>
  `
}

function renderTabPanel(optionId, contentMarkup, isHidden = false, withAriaLabelledBy = true) {
  const labelledBy = withAriaLabelledBy ? `aria-labelledby="sg-options-tab-${optionId}"` : ""
  if (isHidden) {
    return /*html*/ `
      <div
        id="sg-options-tab-panel-${optionId}"
        class="sg-options-tab-panel sg-hidden"
        role="tabpanel"
        data-option="${optionId}"
        ${labelledBy}
      >
        ${contentMarkup}
      </div>
    `
  }
  return /*html*/ `
    <div
      id="sg-options-tab-panel-${optionId}"
      class="sg-options-tab-panel"
      role="tabpanel"
      data-option="${optionId}"
      ${labelledBy}
    >
      ${contentMarkup}
    </div>
  `
}

function renderOptionsTabs() {
  const CONTEXT_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 17 0z"></path><path d="M8 10h8"></path><path d="M8 14h5"></path></svg>`
  const SAVE_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>`
  const GENERAL_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9l-3.8 3.8z"></path></svg>`
  const IMAGE_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sg-icon-sm" aria-hidden="true"><path d="M3 3h18v18H3z"></path><path d="M8 15l3-3 2 2 3-3 5 5"></path><circle cx="9" cy="9" r="1.5"></circle></svg>`

  const tabs = [
    { optionId: "context", title: CONTEXT_ICON, ariaLabel: "Kontext", contentMarkup: "<sg-input-context></sg-input-context>", isSelected: true },
    { optionId: "image", title: IMAGE_ICON, ariaLabel: "Bild", contentMarkup: "<sg-input-image></sg-input-image>" },
    { optionId: "history", title: SAVE_ICON, ariaLabel: "Zwischenstände", contentMarkup: "<sg-input-history></sg-input-history>" },
    { optionId: "general", title: GENERAL_ICON, ariaLabel: "Allgemein", contentMarkup: "<sg-input-general></sg-input-general>" },
  ]
  const tabsMarkup = tabs
    .map((tab) => renderTab(tab.optionId, tab.title, Boolean(tab.isSelected), tab.ariaLabel || ""))
    .join("")
  const panelsMarkup = tabs.map((tab) => renderTabPanel(tab.optionId, tab.contentMarkup)).join("")

  // Creator panels without own tab buttons
  const sceneCreatorPanel = renderTabPanel(SCENE_CREATOR_OPTION_ID, "<sg-input-scene></sg-input-scene>", true, false)
  const npcCreatorPanel = renderTabPanel(NPC_CREATOR_OPTION_ID, "<sg-input-npc></sg-input-npc>", true, false)

  return /*html*/ `
    <div class="sg-options-tab-panels">
      ${panelsMarkup}
      ${sceneCreatorPanel}
      ${npcCreatorPanel}
    </div>
    <div class="sg-options-tabs-list" role="tablist" aria-label="Optionen">
      ${tabsMarkup}
    </div>
  `
}

class SocialGameInput extends HTMLElement {
  constructor() {
    super()
    this._state = {
      isSending: false,
      isSessionLoading: false,
      isSelectorPanelOpen: false,
    }

    this.$ = {}
    this._activeTabOption = "context"
    this._outsideClickEvents = null
  }

  connectedCallback() {
    const optionsTabs = renderOptionsTabs()

    this.innerHTML = /*html*/ `
      <form class="sg-chat-form" aria-busy="false">
        <div id="sg-options-panel" class="sg-options-panel sg-hidden">
          ${optionsTabs}
        </div>
        <sg-input-composer></sg-input-composer>
      </form>
    `

    this.$ = {
      form: this.querySelector(".sg-chat-form"),
      optionsPanel: this.querySelector(".sg-options-panel"),
      composer: this.querySelector("sg-input-composer"),
      sceneCreatorPanel: this.querySelector(`.sg-options-tab-panel[data-option="${SCENE_CREATOR_OPTION_ID}"]`),
      npcCreatorPanel: this.querySelector(`.sg-options-tab-panel[data-option="${NPC_CREATOR_OPTION_ID}"]`),
      tabEntries: this.collectTabEntries(),
    }

    this.registerTabEvents()
    this.registerCreatorEvents()
    this.registerOutsideClickClose()
    this.syncTabState()
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
  }

  disconnectedCallback() {
    this._outsideClickEvents?.abort()
    this._outsideClickEvents = null
  }

  collectTabEntries() {
    const tabs = Array.from(this.querySelectorAll(".sg-options-tab"))
    return tabs.map((tab) => {
      const optionId = tab.dataset.option || ""
      return {
        optionId,
        tab,
        panel: this.querySelector(`.sg-options-tab-panel[data-option="${optionId}"]`),
      }
    })
  }

  registerTabEvents() {
    for (const entry of this.$.tabEntries) {
      entry.tab.addEventListener("click", this.onTabClick.bind(this))
    }
  }

  registerCreatorEvents() {
    this.$.optionsPanel.addEventListener("createSceneRequested", this.onCreateSceneRequested.bind(this))
    this.$.optionsPanel.addEventListener("sceneCreateFinished", this.onSceneCreateFinished.bind(this))
    this.$.optionsPanel.addEventListener("createNpcRequested", this.onCreateNpcRequested.bind(this))
    this.$.optionsPanel.addEventListener("npcCreateFinished", this.onNpcCreateFinished.bind(this))
  }

  registerOutsideClickClose() {
    const controller = new AbortController()
    this._outsideClickEvents?.abort()
    this._outsideClickEvents = controller
    document.addEventListener("pointerdown", this.onDocumentPointerDown.bind(this), {
      signal: controller.signal,
      capture: true,
    })
  }

  onDocumentPointerDown(event) {
    if (!this._state.isSelectorPanelOpen) {
      return
    }

    if (this.contains(event.target)) {
      return
    }

    appStore.setState({ isSelectorPanelOpen: false })
  }

  onTabClick(event) {
    const nextOptionId = event.currentTarget.dataset.option || ""
    if (!nextOptionId || nextOptionId === this._activeTabOption) {
      return
    }

    this._activeTabOption = nextOptionId
    this.syncTabState()
  }

  onCreateSceneRequested() {
    if (this._activeTabOption === SCENE_CREATOR_OPTION_ID) {
      return
    }
    this._activeTabOption = SCENE_CREATOR_OPTION_ID
    this.syncTabState()
  }

  onSceneCreateFinished() {
    this._activeTabOption = "context"
    this.syncTabState()
  }

  onCreateNpcRequested() {
    if (this._activeTabOption === NPC_CREATOR_OPTION_ID) {
      return
    }
    this._activeTabOption = NPC_CREATOR_OPTION_ID
    this.syncTabState()
  }

  onNpcCreateFinished() {
    this._activeTabOption = "context"
    this.syncTabState()
  }

  syncTabState() {
    const isSceneCreatorActive = this._activeTabOption === SCENE_CREATOR_OPTION_ID
    const isNpcCreatorActive = this._activeTabOption === NPC_CREATOR_OPTION_ID
    const isCreatorActive = isSceneCreatorActive || isNpcCreatorActive
    for (const entry of this.$.tabEntries) {
      const isSelected = !isCreatorActive && entry.optionId === this._activeTabOption
      this.setTabEntrySelectedState(entry, isSelected)
      if (entry.panel) {
        entry.panel.hidden = isCreatorActive || !isSelected
      }
    }

    this.$.sceneCreatorPanel.classList.toggle("sg-hidden", !isSceneCreatorActive)
    this.$.sceneCreatorPanel.hidden = !isSceneCreatorActive
    this.$.npcCreatorPanel.classList.toggle("sg-hidden", !isNpcCreatorActive)
    this.$.npcCreatorPanel.hidden = !isNpcCreatorActive
  }

  setTabEntrySelectedState(entry, isSelected) {
    entry.tab.setAttribute("aria-selected", isSelected ? "true" : "false")
    entry.tab.tabIndex = isSelected ? 0 : -1
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.isSending = Boolean(state.isSending)
    this._state.isSessionLoading = Boolean(state.isSessionLoading)
    this._state.isSelectorPanelOpen = Boolean(state.isSelectorPanelOpen)
  }

  registerSubscriptions() {
    const subscriptions = [
      ["isSending", this.onIsSendingChanged.bind(this)],
      ["isSessionLoading", this.onSessionLoadingChanged.bind(this)],
      ["isSelectorPanelOpen", this.onSelectorPanelChanged.bind(this)],
    ]

    for (const [key, listener] of subscriptions) {
      appStore.subscribe(key, listener)
    }
  }

  onIsSendingChanged(isSending) {
    this._state.isSending = Boolean(isSending)
    this.render()
  }

  onSessionLoadingChanged(isSessionLoading) {
    this._state.isSessionLoading = Boolean(isSessionLoading)
    this.render()
  }

  onSelectorPanelChanged(isSelectorPanelOpen) {
    this._state.isSelectorPanelOpen = Boolean(isSelectorPanelOpen)
    this.render()
  }

  focusInput() {
    this.$.composer.focusInput()
  }

  render() {
    const controlsDisabled = this._state.isSending || this._state.isSessionLoading

    this.$.form.setAttribute("aria-busy", controlsDisabled ? "true" : "false")
    this.$.form.classList.toggle("is-options-open", this._state.isSelectorPanelOpen)
    this.$.optionsPanel.classList.toggle("sg-hidden", !this._state.isSelectorPanelOpen)
  }
}

customElements.get("sg-input") || customElements.define("sg-input", SocialGameInput)
