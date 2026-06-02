import type { FormEvent, KeyboardEvent, ReactNode, RefObject } from "react"
import { Link } from "react-router-dom"
import type { AppView } from "../../state/appViewTypes"
import { GearIcon, SendIcon } from "../../shared/icons"
import { SceneImageContainer } from "../image/SceneImageContainer"

type ComposerViewProps = {
  input: string
  inputRef: RefObject<HTMLTextAreaElement | null>
  isLoading: boolean
  isOptionsOpen: boolean
  isStreaming: boolean
  error: string
  optionsHref: string
  appView?: AppView
  optionsPanel: ReactNode
  onInput: (value: string) => void
  onSubmit: () => void
}

export function ComposerView(props: ComposerViewProps) {
  const formBusy = props.isStreaming || props.isLoading

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void props.onSubmit()
  }

  return (
    <section className="sg-input-component">
      <form
        className={`sg-chat-form ${props.isOptionsOpen ? "is-options-open" : ""}`}
        aria-busy={formBusy ? "true" : "false"}
        onSubmit={handleSubmit}
      >
        {props.optionsPanel}
        <div className="sg-composer-layout">
          {!props.isOptionsOpen ? <SceneImageContainer className="sg-composer-thumb" appView={props.appView} /> : null}
          <div className="sg-composer-main">
            <div className="sg-composer-row">
              <label htmlFor="sg-chat-input" className="sg-visually-hidden">
                Nachricht eingeben
              </label>
              <textarea
                id="sg-chat-input"
                className="sg-chat-input sg-chat-textarea"
                rows={1}
                placeholder="Nachricht eingeben..."
                ref={props.inputRef}
                value={props.input}
                readOnly={props.isLoading}
                aria-readonly={props.isLoading ? "true" : "false"}
                onChange={(event) => props.onInput(event.currentTarget.value)}
                onKeyDown={(event) => handleKey(event, props.onSubmit)}
              />
              <button
                type="submit"
                className={`sg-send-button ${props.isStreaming ? "is-loading" : ""}`}
                aria-label="Senden"
                disabled={props.isLoading}
              >
                <SendIcon />
              </button>
            </div>
            <div className="sg-composer-footer">
              <div className="sg-composer-meta" role="status" aria-live="polite">
                {props.isStreaming ? (
                  <StreamingStatus />
                ) : !props.isOptionsOpen ? (
                  <span className="sg-keyboard-hint">Enter = senden, Shift+Enter = neue Zeile</span>
                ) : null}
              </div>
              <div className="sg-composer-tools" aria-label="Werkzeuge">
                <Link className="sg-options-toggle" aria-label="Optionen" to={props.optionsHref}>
                  <GearIcon /> Optionen
                </Link>
              </div>
            </div>
          </div>
        </div>
        {props.error ? (
          <div className="sg-composer-error-container" role="alert">
            <span className="sg-composer-error">{props.error}</span>
          </div>
        ) : null}
      </form>
    </section>
  )
}

function StreamingStatus() {
  return (
    <span className="sg-composer-status" aria-label="Antwort wird geladen">
      <span className="typing-dots" aria-hidden="true">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </span>
      <span className="sg-visually-hidden">Antwort wird geladen</span>
    </span>
  )
}

function handleKey(event: KeyboardEvent<HTMLTextAreaElement>, submit: () => void) {
  if (event.key !== "Enter" || event.shiftKey) return
  event.preventDefault()
  void submit()
}
