import { appActions } from "./app-actions.js"
import { appStore } from "./app-store.js"
import { RESTORE_ICON, SAVE_ICON } from "./icons.js"
import "./sg-settings-action.js"

function isAutoBackup(checkpoint) {
  return checkpoint.commit_message.includes("[auto-backup]")
}

function renderCheckpointItem(checkpoint) {
  const autoBackup = isAutoBackup(checkpoint)
  const label = autoBackup ? checkpoint.commit_message.replace("[auto-backup]", "").trim() : checkpoint.commit_message
  return /*html*/ `
    <button
      type="button"
      class="sg-checkpoint-item${autoBackup ? " sg-checkpoint-item--auto-backup" : ""}"
      data-commit-hash="${checkpoint.commit_hash}"
      aria-label="Checkpoint: ${label}"
    >
      <span class="sg-checkpoint-item-icon" aria-hidden="true">${RESTORE_ICON}</span>
      <span class="sg-checkpoint-item-body">
        <span class="sg-checkpoint-title">${label}</span>
        <span class="sg-checkpoint-date">${checkpoint.commit_date}${autoBackup ? " · Auto-Backup" : ""}</span>
      </span>
    </button>
  `
}

class SocialGameInputHistory extends HTMLElement {
  constructor() {
    super()
    this._state = {
      isHistoryLoading: false,
      historyError: "",
      checkpoints: [],
    }

    this.$ = {}
  }

  connectedCallback() {
    this.innerHTML = /*html*/ `
      <section class="sg-settings-section">
        <h3 class="sg-settings-heading">Zwischenstände</h3>
        <div class="sg-checkpoint-list-container">
          <div class="sg-checkpoint-list" role="region" aria-label="Gespeicherte Spielstände"></div>
          <div class="sg-checkpoint-empty sg-hidden">
            Keine Spielstände vorhanden
          </div>
        </div>
        <div class="sg-checkpoint-error sg-hidden"></div>
        <sg-settings-action
          data-action="save-history"
          aria-label="Zwischenstand speichern"
        >
            <span slot="icon">${SAVE_ICON}</span>
            <span>Zwischenstand speichern</span>
            <span slot="description">Speichert den aktuellen Stand als wiederherstellbaren Checkpoint</span>
        </sg-settings-action>
      </section>
    `

    this.$ = {
      saveButton: this.querySelector('[data-action="save-history"]'),
      checkpointList: this.querySelector(".sg-checkpoint-list"),
      checkpointEmpty: this.querySelector(".sg-checkpoint-empty"),
      checkpointError: this.querySelector(".sg-checkpoint-error"),
    }

    this.$.saveButton.addEventListener("click", this.handleSaveClick.bind(this))
    this.registerSubscriptions()
    this.syncFromStore()
    this.render()
    appActions.loadCheckpoints()
    this.$.saveButton.focus()
  }

  syncFromStore() {
    const state = appStore.getState()
    this._state.isHistoryLoading = Boolean(state.isHistoryLoading)
    this._state.historyError = typeof state.historyError === "string" ? state.historyError : ""
    this._state.checkpoints = Array.isArray(state.checkpoints) ? state.checkpoints : []
  }

  registerSubscriptions() {
    appStore.subscribe("checkpoints", this.onCheckpointsChanged.bind(this))
    appStore.subscribe("historyError", this.onHistoryErrorChanged.bind(this))
    appStore.subscribe("isHistoryLoading", this.onHistoryLoadingChanged.bind(this))
  }

  onCheckpointsChanged() {
    const { checkpoints } = appStore.getState()
    this._state.checkpoints = Array.isArray(checkpoints) ? checkpoints : []
    this.renderCheckpoints()
  }

  onHistoryErrorChanged() {
    const { historyError } = appStore.getState()
    this._state.historyError = typeof historyError === "string" ? historyError : ""
    this.renderCheckpoints()
  }

  onHistoryLoadingChanged() {
    this._state.isHistoryLoading = Boolean(appStore.getState().isHistoryLoading)
    this.render()
  }

  async handleSaveClick() {
    await appActions.saveCheckpoint()
  }

  renderCheckpoints() {
    const hasError = this._state.historyError.trim()
    const hasCheckpoints = this._state.checkpoints.length > 0

    this.$.checkpointEmpty.classList.toggle("sg-hidden", hasCheckpoints || Boolean(hasError))
    this.$.checkpointError.classList.toggle("sg-hidden", !hasError)

    if (hasError) {
      this.$.checkpointError.textContent = this._state.historyError
    }

    if (hasCheckpoints) {
      const markup = this._state.checkpoints.map(cp => renderCheckpointItem(cp)).join("")
      this.$.checkpointList.innerHTML = markup

      this.$.checkpointList.querySelectorAll(".sg-checkpoint-item").forEach((button) => {
        button.addEventListener("click", this.handleRestoreClick.bind(this))
      })
    } else if (!hasError) {
      this.$.checkpointList.innerHTML = ""
    }
  }

  async handleRestoreClick(event) {
    const button = event.currentTarget
    const commitHash = button.dataset.commitHash
    if (commitHash) {
      await appActions.restoreCheckpoint(commitHash)
    }
  }

  render() {
    this.$.saveButton.disabled = this._state.isHistoryLoading
    this.renderCheckpoints()
  }
}

customElements.get("sg-input-history") || customElements.define("sg-input-history", SocialGameInputHistory)
