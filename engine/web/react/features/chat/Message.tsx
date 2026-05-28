import type { ChatMessage } from "../../api/types"
import { PencilIcon, TextEditIcon } from "../../shared/icons"
import { buildOptionsPath } from "../options/routes"
import { useStateQuery } from "../../api/state"
import { Link } from "react-router-dom"

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
  const html = typeof message.html === "string" ? sanitizeHtml(message.html) : ""
  const text = message.content || ""
  const hrefSceneContext = data?.npcId && data.sceneId ? buildOptionsPath(data.npcId, data.sceneId, "scene-context") : "/"
  const hrefSceneEditor = data?.npcId && data.sceneId ? buildOptionsPath(data.npcId, data.sceneId, "scene-editor") : "/"

  return (
    <div className="context-rich msg-context msg-bubble msg-bubble-context">
      {html ? (
        <div className="sg-initial-context-html" dangerouslySetInnerHTML={{ __html: html }} />
      ) : (
        <div className="sg-initial-context-html msg-content-prewrap">{text}</div>
      )}
      {message.is_editable_scene_context ? (
        <div className="sg-context-message-actions">
          <Link className="sg-context-message-edit" aria-label="Szenenkontext bearbeiten" to={hrefSceneContext}>
            <PencilIcon />
          </Link>
          <Link className="sg-context-message-edit" aria-label="Event Location bearbeiten" to={hrefSceneEditor}>
            <TextEditIcon />
          </Link>
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

function sanitizeHtml(html: string) {
  const template = document.createElement("template")
  template.innerHTML = html

  for (const element of Array.from(template.content.querySelectorAll("script, style, iframe, object, embed, link, meta, base"))) {
    element.remove()
  }

  for (const element of Array.from(template.content.querySelectorAll("*"))) {
    for (const attribute of Array.from(element.attributes)) {
      const name = attribute.name.toLowerCase()
      const value = attribute.value.trim().toLowerCase()
      if (name.startsWith("on")) {
        element.removeAttribute(attribute.name)
        continue
      }
      if ((name === "href" || name === "src" || name === "xlink:href" || name === "formaction") && value.startsWith("javascript:")) {
        element.removeAttribute(attribute.name)
      }
    }
  }

  return template.innerHTML.trim()
}
