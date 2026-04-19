import { appStore } from "./app-store.js"
import "./sg-input-context.js"
import "./sg-input-image.js"
import "./sg-input-general.js"
import "./sg-input-composer.js"

function renderTab(optionId, title, isSelected = false) {
  const selected = isSelected ? "true" : "false"
  const tabIndex = isSelected ? "0" : "-1"
  return `
    <button
      type="button"
      class="sg-options-tab"
      role="tab"
      id="sg-options-tab-${optionId}"
      data-option="${optionId}"
      aria-selected="${selected}"
      aria-controls="sg-options-tab-panel-${optionId}"
      tabindex="${tabIndex}"
    >
      ${title}
    </button>
  `
}

function renderTabPanel(optionId, contentMarkup) {
  return `
    <div
      id="sg-options-tab-panel-${optionId}"
      class="sg-options-tab-panel"
      role="tabpanel"
      data-option="${optionId}"
      aria-labelledby="sg-options-tab-${optionId}"
    >
      ${contentMarkup}
    </div>
  `
}

function renderOptionsTabs() {
  const tabs = [
    { optionId: "context", title: "Kontext", contentMarkup: "<sg-input-context></sg-input-context>", isSelected: true },
    { optionId: "image", title: "Bild", contentMarkup: "<sg-input-image></sg-input-image>" },
    { optionId: "general", title: "Allgemein", contentMarkup: "<sg-input-general></sg-input-general>" },
  ]
  const tabsMarkup = tabs.map((tab) => renderTab(tab.optionId, tab.title, Boolean(tab.isSelected))).join("")
  const panelsMarkup = tabs.map((tab) => renderTabPanel(tab.optionId, tab.contentMarkup)).join("")

  return `
    <div class="sg-options-tab-panels">
      ${panelsMarkup}
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

    this.innerHTML = `
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
      tabEntries: this.collectTabEntries(),
    }

    this.registerTabEvents()
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

  syncTabState() {
    for (const entry of this.$.tabEntries) {
      const isSelected = entry.optionId === this._activeTabOption
      this.setTabEntrySelectedState(entry, isSelected)
    }
  }

  setTabEntrySelectedState(entry, isSelected) {
    entry.tab.setAttribute("aria-selected", isSelected ? "true" : "false")
    entry.tab.tabIndex = isSelected ? 0 : -1
    if (entry.panel) {
      entry.panel.hidden = !isSelected
    }
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
