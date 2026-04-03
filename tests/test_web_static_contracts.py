from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT_DIR / rel_path).read_text(encoding="utf-8")


def test_sg_message_sanitizes_html_before_innerhtml_assignment():
    source = _read("engine/web/static/js/sg-message.js")

    assert "function sanitizeMessageHtml(rawHtml)" in source
    assert "name.startsWith(\"on\")" in source
    assert "javascript:" in source
    assert "contentMarkup = sanitizeMessageHtml(message.html)" in source
    assert "contentMarkup = message.html" not in source


def test_sg_message_sanitizer_uses_domparser_not_template_innerhtml():
    source = _read("engine/web/static/js/sg-message.js")

    assert "DOMParser" in source
    assert "template.innerHTML" not in source


def test_trusted_types_policy_is_defined():
    source = _read("engine/web/static/js/trusted-types.js")

    assert "trustedTypes.createPolicy" in source
    assert '"sg"' in source
    assert "export function trustedHtml" in source


def test_all_components_use_trusted_html_for_innerhtml():
    for rel_path in (
        "engine/web/static/js/sg-app.js",
        "engine/web/static/js/sg-chat.js",
        "engine/web/static/js/sg-context-message.js",
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


def test_sg_chat_exposes_public_messages_api_methods():
    source = _read("engine/web/static/js/sg-chat.js")

    expected_methods = [
        "addMessagesScrollListener(",
        "removeMessagesScrollListener(",
        "isMessagesNearBottom(",
        "scrollMessagesToBottom(",
        "observeMessagesResize(",
        "observeMessagesMutations(",
    ]

    for method in expected_methods:
        assert method in source


def test_sg_chat_routes_context_messages_to_context_component():
    source = _read("engine/web/static/js/sg-chat.js")

    assert 'import "./sg-context-message.js"' in source
    assert '"sg-context-message"' in source
    assert '"context-character"' in source
    assert '"context-scene"' in source


def test_sg_app_uses_sg_chat_public_api_instead_of_internal_dom_access():
    source = _read("engine/web/static/js/sg-app.js")

    assert 'querySelector(".sg-chat-messages")' not in source
    assert "addMessagesScrollListener" in source
    assert "removeMessagesScrollListener" in source
    assert "isMessagesNearBottom" in source
    assert "scrollMessagesToBottom" in source
    assert "observeMessagesResize" in source
    assert "observeMessagesMutations" in source

