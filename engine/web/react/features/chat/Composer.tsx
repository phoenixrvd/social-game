import { useEffect, useLayoutEffect, useRef, useState } from "react"
import type { FormEvent, KeyboardEvent, RefObject } from "react"
import { Link } from "react-router-dom"
import { useStateQuery } from "../../api/state"
import { GearIcon, SendIcon } from "../../shared/icons"
import { SceneImage } from "../image/SceneImage"
import { buildOptionsPath, useOptionsParams } from "../options/routes"
import { OptionsRoute } from "../options/OptionsRoute"
import { useChatStream } from "./useChatStream"

type ComposerProps = {
  inputRef: RefObject<HTMLTextAreaElement | null>
  chat: ReturnType<typeof useChatStream>
}

export function Composer({ inputRef, chat }: ComposerProps) {
  const { data, isLoading } = useStateQuery()
  const [input, setInput] = useState("")
  const formRef = useRef<HTMLFormElement | null>(null)
  const options = useOptionsParams()
  const formBusy = chat.isSending || isLoading
  const npcId = options.npcId || data?.npcId || data?.defaultNpcId
  const sceneId = options.sceneId || data?.sceneId || data?.defaultSceneId
  const optionsHref = npcId && sceneId ? buildOptionsPath(npcId, sceneId, "context") : "/"
  const toggleHref = options.isOptionsRoute ? "/" : optionsHref

  useLayoutEffect(() => {
    const textarea = inputRef.current
    if (!textarea) return
    textarea.style.height = "auto"
    textarea.style.height = `${Math.max(textarea.scrollHeight, 46)}px`
  }, [input, inputRef])

  useEffect(() => {
    if (!options.isOptionsRoute) return

    function closeOptionsOnOutsidePointer(event: PointerEvent) {
      const target = event.target
      if (!(target instanceof Node)) return
      if (formRef.current?.contains(target)) return
      if (target instanceof Element && target.closest(".sg-confirm-backdrop")) return
      options.close()
    }

    document.addEventListener("pointerdown", closeOptionsOnOutsidePointer)
    return () => document.removeEventListener("pointerdown", closeOptionsOnOutsidePointer)
  }, [options])

  async function submit() {
    const text = input.trim()
    if (!text) return
    setInput("")
    await chat.submit(text)
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void submit()
  }

  return (
    <section className="sg-input-component">
      <form ref={formRef} className={`sg-chat-form ${options.isOptionsRoute ? "is-options-open" : ""}`} aria-busy={formBusy ? "true" : "false"} onSubmit={handleSubmit}>
        <OptionsRoute />
        <div className="sg-composer-layout">
          {!options.isOptionsRoute ? <SceneImage className="sg-composer-thumb" imageState={data} /> : null}
          <div className="sg-composer-main">
            <div className="sg-composer-row">
              <label htmlFor="sg-chat-input" className="sg-visually-hidden">Nachricht eingeben</label>
              <textarea
                id="sg-chat-input"
                className="sg-chat-input sg-chat-textarea"
                rows={1}
                placeholder="Nachricht eingeben..."
                ref={inputRef}
                value={input}
                readOnly={isLoading}
                aria-readonly={isLoading ? "true" : "false"}
                onChange={(event) => setInput(event.currentTarget.value)}
                onKeyDown={(event) => handleKey(event, submit)}
              />
              <button type="submit" className={`sg-send-button ${chat.isSending ? "is-loading" : ""}`} aria-label="Senden" disabled={isLoading}>
                <SendIcon />
              </button>
            </div>
            <div className="sg-composer-footer">
              <div className="sg-composer-meta" role="status" aria-live="polite">
                {chat.isSending ? <span className="sg-composer-status">Antwort wird geladen</span> : <span className="sg-keyboard-hint">Enter = senden, Shift+Enter = neue Zeile</span>}
              </div>
              <div className="sg-composer-tools" aria-label="Werkzeuge">
                <Link className="sg-options-toggle" aria-label="Optionen" to={toggleHref}><GearIcon /> Optionen</Link>
              </div>
            </div>
          </div>
        </div>
        {chat.error ? <div className="sg-composer-error-container" role="alert"><span className="sg-composer-error">{chat.error}</span></div> : null}
      </form>
    </section>
  )
}

function handleKey(event: KeyboardEvent<HTMLTextAreaElement>, submit: () => void) {
  if (event.key !== "Enter" || event.shiftKey) return
  event.preventDefault()
  void submit()
}
