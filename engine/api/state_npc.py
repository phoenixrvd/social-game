from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from typing import Any

import markdown
import yaml

from engine.storage.models import Message

VISIBLE_CHAT_ROLES = {"user", "assistant"}


def render_markdown_to_html(text: str) -> str:
    return markdown.markdown(text, extensions=["extra", "sane_lists"])


def parse_state_meta(state_text: str) -> tuple[dict[str, Any], str]:
    parser = markdown.Markdown(extensions=["meta", "extra", "sane_lists"])
    body_html = parser.convert(state_text)
    raw_meta = getattr(parser, "Meta", {})
    meta_values: dict[str, Any] = {}
    for key, values in raw_meta.items():
        raw_value = "\n".join(values).strip() if isinstance(values, list) else str(values).strip()
        if not raw_value:
            continue
        meta_values[key] = yaml.safe_load(raw_value)
    return meta_values, body_html


def dump_state_meta_yaml(meta_values: dict[str, Any]) -> str:
    if not meta_values:
        return ""
    return yaml.safe_dump(meta_values, sort_keys=False, allow_unicode=True).strip()


def render_state_to_html(state_text: str) -> str:
    meta_values, body_html = parse_state_meta(state_text)
    html_parts = [render_markdown_to_html("# Beziehung")]
    meta_yaml = dump_state_meta_yaml(meta_values)
    if meta_yaml:
        html_parts.append(f"<pre>{escape(meta_yaml)}</pre>")
    if body_html.strip():
        html_parts.append(body_html)
    return "\n".join(html_parts)


def visible_messages(npc, scene) -> list[dict[str, Any]]:
    visible = [m.model_dump() for m in npc.stm.get() if m.role in VISIBLE_CHAT_ROLES]
    if visible:
        return visible
    now = datetime.now(UTC)
    character_description = npc.description.get()
    npc_state = npc.state.strip()
    scene_description = scene.description.strip() or "Keine Szenenbeschreibung verfügbar."
    return [
        {
            "id": "context-character",
            "role": "assistant",
            "content": "",
            "html": render_markdown_to_html(character_description),
            "timestamp_utc": now,
        },
        {
            "id": "context-scene",
            "role": "assistant",
            "content": "",
            "html": render_markdown_to_html(scene_description),
            "timestamp_utc": now,
            "context_type": "scene",
            "is_editable_scene_context": True,
        },
        {
            "id": "context-state",
            "role": "assistant",
            "content": "",
            "html": render_state_to_html(npc_state),
            "timestamp_utc": now,
        },
    ]


def visible_stm_messages(npc) -> list[Message]:
    return [m for m in npc.stm.get() if m.role in VISIBLE_CHAT_ROLES]


def messages_signature(npc) -> str:
    visible = visible_stm_messages(npc)
    last_id = visible[-1].id if visible else ""
    return f"{len(visible)}|{last_id}"
