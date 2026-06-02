import { createContext, useContext, useEffect, useState } from "react"
import type { ReactNode } from "react"

type ConfirmOptions = {
  title?: string
  message: string
  listItems?: string[]
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
}

type ConfirmRequest = {
  options: Required<ConfirmOptions>
  resolve: (accepted: boolean) => void
}

const ConfirmContext = createContext<((options: ConfirmOptions) => Promise<boolean>) | null>(null)

export function ConfirmDialogProvider({ children }: { children: ReactNode }) {
  const [request, setRequest] = useState<ConfirmRequest | null>(null)

  function confirm(options: ConfirmOptions) {
    return new Promise<boolean>((resolve) => {
      setRequest({
        resolve,
        options: {
          title: options.title || "Bitte bestätigen",
          message: options.message,
          listItems: options.listItems || [],
          confirmLabel: options.confirmLabel || "Bestätigen",
          cancelLabel: options.cancelLabel || "Abbrechen",
          danger: Boolean(options.danger),
        },
      })
    })
  }

  function onKeyDown(event: KeyboardEvent) {
    if (event.key !== "Escape") return
    event.preventDefault()
    close(false)
  }

  useEffect(() => {
    if (!request) return
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [request])

  function close(accepted: boolean) {
    request?.resolve(accepted)
    setRequest(null)
  }

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {request ? (
        <div className="sg-confirm-backdrop" role="presentation" onClick={() => close(false)}>
          <div
            className="sg-confirm-dialog"
            role="dialog"
            aria-modal="true"
            onClick={(event) => event.stopPropagation()}
          >
            <h3 className="sg-settings-heading">{request.options.title}</h3>
            <p className="sg-confirm-message">{request.options.message}</p>
            {request.options.listItems.length > 0 ? (
              <ul className="sg-confirm-list">
                {request.options.listItems.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}
            <div className="sg-settings-actions">
              <span className="sg-settings-action">
                <button type="button" className="sg-settings-action-button" onClick={() => close(false)}>
                  {request.options.cancelLabel}
                </button>
              </span>
              <span className={`sg-settings-action ${request.options.danger ? "danger" : ""}`}>
                <button type="button" className="sg-settings-action-button" onClick={() => close(true)}>
                  {request.options.confirmLabel}
                </button>
              </span>
            </div>
          </div>
        </div>
      ) : null}
    </ConfirmContext.Provider>
  )
}

export function useConfirmDialog() {
  const context = useContext(ConfirmContext)
  if (!context) throw new Error("useConfirmDialog muss innerhalb von ConfirmDialogProvider verwendet werden")
  return context
}
