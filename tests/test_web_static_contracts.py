from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT_DIR / rel_path).read_text(encoding="utf-8")


def test_sg_message_uses_content_only_rendering():
    source = _read("engine/web/static/js/sg-message.js")

    assert "message.content" in source
    assert "message.html" not in source
    assert "msg-content-prewrap" in source
    assert "console.log(" not in source


def test_sg_message_has_no_domparser_sanitizer_path():
    source = _read("engine/web/static/js/sg-message.js")

    assert "sanitizeMessageHtml(" not in source
    assert "DOMParser" not in source
    assert "template.innerHTML" not in source


def test_trusted_types_policy_is_defined():
    source = _read("engine/web/static/js/trusted-types.js")

    assert "trustedTypes.createPolicy" in source
    assert '"sg"' in source
    assert "export function trustedHtml" in source


def test_components_with_direct_html_injection_use_trusted_html():
    for rel_path in (
        "engine/web/static/js/sg-chat.js",
        "engine/web/static/js/sg-input.js",
        "engine/web/static/js/sg-scene-image.js",
        "engine/web/static/js/sg-message.js",
    ):
        source = _read(rel_path)
        assert 'from "./trusted-types.js"' in source, f"{rel_path} importiert trusted-types nicht"
        assert "trustedHtml(" in source, f"{rel_path} verwendet kein trustedHtml"


def test_index_has_no_inline_scripts():
    source = _read("engine/web/static/index.html")

    assert "<script>" not in source
    assert "theme-init.js" in source


def test_sg_chat_exposes_scroll_method():
    source = _read("engine/web/static/js/sg-chat.js")

    assert "scrollMessagesToBottom(" in source


def test_sg_chat_updates_existing_message_elements_during_sync():
    source = _read("engine/web/static/js/sg-chat.js")

    assert "element.message = renderedMessage" in source
    assert "container.insertBefore(element, referenceNode)\n        element.message = renderedMessage" not in source


def test_sg_chat_routes_context_messages_to_context_component():
    source = _read("engine/web/static/js/sg-chat.js")

    assert 'import "./sg-context-message.js"' in source
    assert '"sg-context-message"' in source
    assert '"context-character"' in source
    assert '"context-scene"' in source


def test_sg_input_keeps_focus_stable_while_sending():
    source = _read("engine/web/static/js/sg-input.js")

    assert "const composerReadOnly = this._state.isSessionLoading" in source
    assert "this.$.textarea.readOnly = composerReadOnly" in source
    assert "this.$.textarea.setAttribute(\"aria-readonly\", composerReadOnly ? \"true\" : \"false\")" in source
    assert "this.$.sendButton.addEventListener(\"pointerdown\", this.handleSendPointerDown.bind(this))" in source
    assert "handleSendPointerDown(event)" in source
    assert "event.preventDefault()" in source
    assert "isSubmitBlocked()" in source
    assert "return this._state.isSending || this._state.isSessionLoading" in source
    assert "if (this.isSubmitBlocked())" in source
    assert "_restoreFocusAfterSend" not in source
    assert "requestAnimationFrame(() => this.focusInput())" not in source
