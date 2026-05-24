import { appStore } from "./app-store.js"
import { CONTEXT_ICON, GENERAL_ICON, IMAGE_ICON, SAVE_ICON } from "./icons.js"
import "./sg-input-context.js"
import "./sg-input-image.js"
import "./sg-input-general.js"
import "./sg-input-scene.js"
import "./sg-input-npc.js"
import "./sg-input-scene-context.js"
import "./sg-input-composer.js"
import "./sg-input-history.js"

const SCENE_CREATOR_OPTION_ID = "scene-creator"
const NPC_CREATOR_OPTION_ID = "npc-creator"
const SCENE_CONTEXT_OPTION_ID = "scene-context"

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
  const sceneContextPanel = renderTabPanel(
    SCENE_CONTEXT_OPTION_ID,
    "<sg-input-scene-context></sg-input-scene-context>",
    true,
    false,
  )

  return /*html*/ `
    <div class="sg-options-tab-panels">
      ${panelsMarkup}
      ${sceneCreatorPanel}
      ${npcCreatorPanel}
      ${sceneContextPanel}
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
      sceneContextPanel: this.querySelector(`.sg-options-tab-panel[data-option="${SCENE_CONTEXT_OPTION_ID}"]`),
      sceneContextInput: this.querySelector("sg-input-scene-context"),
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
    appStore.setState({ activeOptionsPanel: nextOptionId })
    this.syncTabState()
  }

  onCreateSceneRequested() {
    if (this._activeTabOption === SCENE_CREATOR_OPTION_ID) {
      return
    }
    this._activeTabOption = SCENE_CREATOR_OPTION_ID
    appStore.setState({ activeOptionsPanel: SCENE_CREATOR_OPTION_ID })
    this.syncTabState()
  }

  onSceneCreateFinished() {
    this._activeTabOption = "context"
    appStore.setState({ activeOptionsPanel: "context" })
    this.syncTabState()
  }

  onCreateNpcRequested() {
    if (this._activeTabOption === NPC_CREATOR_OPTION_ID) {
      return
    }
    this._activeTabOption = NPC_CREATOR_OPTION_ID
    appStore.setState({ activeOptionsPanel: NPC_CREATOR_OPTION_ID })
    this.syncTabState()
  }

  onNpcCreateFinished() {
    this._activeTabOption = "context"
    appStore.setState({ activeOptionsPanel: "context" })
    this.syncTabState()
  }

  syncTabState() {
    const isSceneCreatorActive = this._activeTabOption === SCENE_CREATOR_OPTION_ID
    const isNpcCreatorActive = this._activeTabOption === NPC_CREATOR_OPTION_ID
    const isSceneContextActive = this._activeTabOption === SCENE_CONTEXT_OPTION_ID
    const isHiddenPanelActive = isSceneCreatorActive || isNpcCreatorActive || isSceneContextActive
    for (const entry of this.$.tabEntries) {
      const isSelected = !isHiddenPanelActive && entry.optionId === this._activeTabOption
      this.setTabEntrySelectedState(entry, isSelected)
      if (entry.panel) {
        entry.panel.hidden = isHiddenPanelActive || !isSelected
      }
    }

    this.$.sceneCreatorPanel.classList.toggle("sg-hidden", !isSceneCreatorActive)
    this.$.sceneCreatorPanel.hidden = !isSceneCreatorActive
    this.$.npcCreatorPanel.classList.toggle("sg-hidden", !isNpcCreatorActive)
    this.$.npcCreatorPanel.hidden = !isNpcCreatorActive
    this.$.sceneContextPanel.classList.toggle("sg-hidden", !isSceneContextActive)
    this.$.sceneContextPanel.hidden = !isSceneContextActive
    if (isSceneContextActive) {
      this.$.sceneContextInput.prepare()
    }
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
      ["activeOptionsPanel", this.onActiveOptionsPanelChanged.bind(this)],
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

  onActiveOptionsPanelChanged(activeOptionsPanel) {
    this._activeTabOption = typeof activeOptionsPanel === "string" && activeOptionsPanel ? activeOptionsPanel : "context"
    this.syncTabState()
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
