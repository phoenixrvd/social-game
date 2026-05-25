import type { ChatMessage } from "../../api/types"
import { PencilIcon } from "../../shared/icons"
import { buildOptionsPath } from "../options/routes"
import { useStateQuery } from "../../api/state"

const CONTEXT_IDS = new Set(["context-character", "context-scene", "context-state"])

export function Message({ message }: { message: ChatMessage }) {
  if (CONTEXT_IDS.has(message.id || "")) return <ContextMessage message={message} />

  const content = typeof message.content === "string" ? message.content : ""
  if (message.role === "assistant" && !content) return null

  const isUser = message.role === "user"
  const roleClass = isUser ? "msg-user msg-bubble-user-align" : "msg-assistant"
  const timeClass = isUser ? "msg-timestamp-user msg-time-user" : "msg-timestamp-assistant msg-time-assistant"

  return (
    <div className={`msg-bubble msg-bubble-standard ${roleClass}`}>
      <div className="msg-content">
        <div className="msg-body msg-content-prewrap">{content}</div>
      </div>
      {message.timestamp_utc ? <div className={`msg-timestamp ${timeClass}`}>{formatTime(message.timestamp_utc)}</div> : null}
    </div>
  )
}

function ContextMessage({ message }: { message: ChatMessage }) {
  const { data } = useStateQuery()
  const text = message.content || htmlToText(message.html || "")
  const href = data?.npcId && data.sceneId ? buildOptionsPath(data.npcId, data.sceneId, "scene-context") : "/"

  return (
    <div className="context-rich msg-context msg-bubble msg-bubble-context">
      <div className="sg-initial-context-html msg-content-prewrap">{text}</div>
      {message.is_editable_scene_context ? (
        <div className="sg-context-message-actions">
          <a className="sg-context-message-edit" aria-label="Scene Context bearbeiten" href={href}>
            <PencilIcon />
          </a>
        </div>
      ) : null}
    </div>
  )
}

function formatTime(timestamp: string) {
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return timestamp
  return new Intl.DateTimeFormat("de-DE", { hour: "2-digit", minute: "2-digit" }).format(date)
}

function htmlToText(html: string) {
  return html
    .replace(/<br\s*\/?\s*>/gi, "\n")
    .replace(/<\/p>/gi, "\n\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .trim()
}
