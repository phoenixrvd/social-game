import type { ReactNode } from "react"

type SettingsActionProps = {
  icon: ReactNode
  title: string
  description?: string
  danger?: boolean
  inactive?: boolean
  compact?: boolean
  disabled?: boolean
  ariaLabel?: string
  ariaPressed?: boolean
  onClick: () => void | Promise<void>
}

export function SettingsAction({
  icon,
  title,
  description,
  danger = false,
  inactive = false,
  compact = false,
  disabled = false,
  ariaLabel,
  ariaPressed,
  onClick,
}: SettingsActionProps) {
  const className = [
    "sg-settings-action",
    danger ? "danger" : "",
    inactive ? "inactive" : "",
    compact ? "compact" : "",
  ].filter(Boolean).join(" ")

  return (
    <span className={className}>
      <button
        type="button"
        className="sg-settings-action-button"
        aria-label={ariaLabel || title}
        aria-pressed={typeof ariaPressed === "boolean" ? ariaPressed : undefined}
        disabled={disabled}
        onClick={() => void onClick()}
      >
        <span className="sg-settings-action-icon">{icon}</span>
        <span className="sg-settings-action-copy">
          <span className="sg-settings-action-title">{title}</span>
          {!compact && description ? <span className="sg-settings-action-text">{description}</span> : null}
        </span>
      </button>
    </span>
  )
}
