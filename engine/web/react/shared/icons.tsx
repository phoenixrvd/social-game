import type { ReactNode } from "react"

type SvgIconProps = {
  children: ReactNode
  size?: "xs" | "sm" | "md"
}

function SvgIcon({ children, size = "sm" }: SvgIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      className={`sg-icon-${size}`}
      aria-hidden="true"
    >
      {children}
    </svg>
  )
}

export function PlusIcon() {
  return (
    <SvgIcon>
      <path d="M12 5v14M5 12h14" />
    </SvgIcon>
  )
}

export function SendIcon() {
  return (
    <SvgIcon size="md">
      <path d="M22 2L11 13" pathLength={1} />
      <path d="M22 2L15 22L11 13L2 9L22 2Z" pathLength={1} />
    </SvgIcon>
  )
}

export function GearIcon() {
  return (
    <SvgIcon size="xs">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </SvgIcon>
  )
}

export function TextEditIcon() {
  return (
    <SvgIcon>
      <path d="M4 7h16M4 12h12M4 17h8" />
    </SvgIcon>
  )
}

export function PencilIcon() {
  return (
    <SvgIcon>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z" />
    </SvgIcon>
  )
}

export function ImageIcon() {
  return (
    <SvgIcon>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m3 16 5-5 4 4 3-3 6 6" />
    </SvgIcon>
  )
}

export function ContextIcon() {
  return (
    <SvgIcon>
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 17 0z" />
      <path d="M8 10h8" />
      <path d="M8 14h5" />
    </SvgIcon>
  )
}

export function SaveIcon() {
  return (
    <SvgIcon>
      <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
      <polyline points="17 21 17 13 7 13 7 21" />
      <polyline points="7 3 7 8 15 8" />
    </SvgIcon>
  )
}

export function GeneralIcon() {
  return (
    <SvgIcon>
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9l-3.8 3.8z" />
    </SvgIcon>
  )
}

export function RefreshIcon() {
  return (
    <SvgIcon>
      <path d="M3 3h18v18H3z" />
      <path d="M3 15l5-5 4 4 3-3 6 6" />
      <path d="M16 8h4v4" />
      <path d="M20 8l-4 4" />
    </SvgIcon>
  )
}

export function RevertIcon() {
  return (
    <SvgIcon>
      <path d="M21 12a9 9 0 1 1-3.1-6.8" />
      <path d="M21 3v6h-6" />
    </SvgIcon>
  )
}

export function RestoreIcon() {
  return (
    <SvgIcon>
      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
    </SvgIcon>
  )
}

export function DeleteIcon() {
  return (
    <SvgIcon>
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14H6L5 6" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
      <path d="M9 6V4h6v2" />
    </SvgIcon>
  )
}

export function CheckedIcon() {
  return (
    <SvgIcon>
      <rect x="3" y="3" width="18" height="18" rx="3" />
      <path d="M7 12l4 4 6-6" />
    </SvgIcon>
  )
}

export function UncheckedIcon() {
  return (
    <SvgIcon>
      <rect x="3" y="3" width="18" height="18" rx="3" />
    </SvgIcon>
  )
}

export function ThemeIcon() {
  return (
    <SvgIcon>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="M4.93 4.93l1.41 1.41" />
      <path d="M17.66 17.66l1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="M6.34 17.66l-1.41 1.41" />
      <path d="M19.07 4.93l-1.41 1.41" />
    </SvgIcon>
  )
}
