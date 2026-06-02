import { Link } from "react-router-dom"
import type { MessageResponse as ChatMessage } from "../../api/generated/model"
import type { MessageView as MessageViewModel } from "../../state/appViewTypes"
import { PencilIcon, TextEditIcon } from "../../shared/icons"
import { SafeHtml } from "./SafeHtml"

const CONTEXT_IDS = new Set(["context-character", "context-scene", "context-state"])

export function MessageView({ message }: { message: ChatMessage | MessageViewModel }) {
  if (CONTEXT_IDS.has(message.id || "")) return <ContextMessageView message={message as MessageViewModel} />

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
      {message.timestampUtc ? (
        <div className={`msg-timestamp ${timeClass}`}>{formatTime(message.timestampUtc)}</div>
      ) : null}
    </div>
  )
}

function ContextMessageView({ message }: { message: MessageViewModel }) {
  const html = typeof message.html === "string" ? message.html : ""
  const text = message.content || ""

  return (
    <div className="context-rich msg-context msg-bubble msg-bubble-context">
      {html ? (
        <SafeHtml className="sg-initial-context-html" html={html} />
      ) : (
        <div className="sg-initial-context-html msg-content-prewrap">{text}</div>
      )}
      {message.isEditableSceneContext && message.contextActions ? (
        <div className="sg-context-message-actions">
          <Link
            className="sg-context-message-edit"
            aria-label="Szenenkontext bearbeiten"
            to={message.contextActions.sceneContextHref}
          >
            <PencilIcon />
          </Link>
          <Link
            className="sg-context-message-edit"
            aria-label="Event Location bearbeiten"
            to={message.contextActions.sceneEditorHref}
          >
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
