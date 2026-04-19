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


def test_trusted_types_helper_is_removed():
    assert not (ROOT_DIR / "engine/web/static/js/trusted-types.js").exists()


def test_components_no_longer_use_trusted_html_helper():
    for rel_path in (
        "engine/web/static/js/sg-chat.js",
        "engine/web/static/js/sg-input.js",
        "engine/web/static/js/sg-input-context.js",
        "engine/web/static/js/sg-input-image.js",
        "engine/web/static/js/sg-input-general.js",
        "engine/web/static/js/sg-input-composer.js",
        "engine/web/static/js/sg-thumbnail.js",
        "engine/web/static/js/sg-message.js",
    ):
        source = _read(rel_path)
        assert 'from "./trusted-types.js"' not in source, f"{rel_path} importiert trusted-types noch"
        assert "trustedHtml(" not in source, f"{rel_path} verwendet trustedHtml noch"


def test_index_has_no_inline_scripts():
    source = _read("engine/web/static/index.html")

    assert "<script>" not in source
    assert "theme-init.js" in source


def test_index_viewport_meta_requests_resized_content_for_mobile_keyboard():
    source = _read("engine/web/static/index.html")

    assert 'interactive-widget=resizes-content' in source


def test_sg_chat_exposes_scroll_method():
    source = _read("engine/web/static/js/sg-chat.js")

    assert "scrollMessagesToBottom(" in source


def test_sg_chat_subscribes_directly_to_messages_only():
    source = _read("engine/web/static/js/sg-chat.js")

    assert 'import { appStore } from "./app-store.js"' in source
    assert '["messages", this.onMessagesChanged.bind(this)]' in source
    assert '["isAssistantTyping", this.onAssistantTypingChanged.bind(this)]' not in source
    assert '["activeAssistantId", this.onActiveAssistantIdChanged.bind(this)]' not in source
    assert "appStore.subscribe(key, listener)" in source
    assert "setState(nextState = {})" not in source


def test_sg_message_renders_only_message_content_without_typing_state():
    source = _read("engine/web/static/js/sg-message.js")

    assert 'import { appStore } from "./app-store.js"' not in source
    assert '["isAssistantTyping", this.onAssistantTypingChanged.bind(this)]' not in source
    assert "typing-dots" not in source
    assert 'message.role === "assistant" && !content' in source
    assert "appStore.getState()" not in source


def test_sg_chat_updates_existing_message_elements_during_sync():
    source = _read("engine/web/static/js/sg-chat.js")

    assert "element.message = message" in source
    assert "renderedMessage" not in source
    assert "isAssistantTypingForActiveMessage" not in source
    assert "container.insertBefore(element, referenceNode)\n      element.message = message" not in source


def test_chat_streaming_logic_is_in_app_actions_and_surfaces_errors():
    source = _read("engine/web/static/js/app-actions.js")

    assert "function parseChatStreamEvent(line)" in source
    assert "JSON.parse(line)" in source
    assert "function appendAssistantChunk(" in source
    assert 'if (event.type === "error")' in source
    assert 'if (event.type === "done")' in source
    assert "if (!isDone)" in source
    assert "assistantMessage" in source
    assert "messages.filter((message) => message.id !== assistantId)" in source


def test_app_store_supports_key_based_subscriptions_and_set_state():
    source = _read("engine/web/static/js/app-store.js")

    assert "_listeners = new Map()" in source
    assert "_globalListeners = new Set()" not in source
    assert "subscribe(key, listener)" in source
    assert "subscribeAll(listener)" not in source
    assert "getState()" in source
    assert "setState(patch = {})" in source
    assert "dispatch(" not in source
    assert "const nextState = { ...prevState, ...(patch || {}) }" in source


def test_app_events_module_no_longer_contains_event_bus():
    assert not (ROOT_DIR / "engine/web/static/js/app-events.js").exists()


def test_sg_chat_routes_context_messages_to_context_component():
    source = _read("engine/web/static/js/sg-chat.js")

    assert 'import "./sg-context-message.js"' in source
    assert '"sg-context-message"' in source
    assert '"context-character"' in source
    assert '"context-scene"' in source
    assert '"context-relationship"' in source


def test_sg_input_keeps_focus_stable_while_sending():
    source = _read("engine/web/static/js/sg-input.js")
    composer_source = _read("engine/web/static/js/sg-input-composer.js")

    assert "focusInput()" in source
    assert "this.$.composer.focusInput()" in source
    assert "this.$.sendButton.addEventListener(\"pointerdown\", this.handleSendPointerDown.bind(this))" in composer_source
    assert "handleSendPointerDown(event)" in composer_source
    assert "event.preventDefault()" in composer_source
    assert "isSubmitBlocked()" in composer_source
    assert "return this._state.isSending || this._state.isSessionLoading" in composer_source
    assert "if (this.isSubmitBlocked())" in composer_source
    assert "_restoreFocusAfterSend" not in source
    assert "requestAnimationFrame(() => this.focusInput())" not in source
    assert "appActions.submitMessage(" in composer_source
    assert "appActions.setInput(" in composer_source
    assert "new CustomEvent(" not in composer_source


def test_sg_input_split_components_handle_actions_directly_without_parent_events():
    source = _read("engine/web/static/js/sg-input.js")
    context_source = _read("engine/web/static/js/sg-input-context.js")
    image_source = _read("engine/web/static/js/sg-input-image.js")
    general_source = _read("engine/web/static/js/sg-input-general.js")
    composer_source = _read("engine/web/static/js/sg-input-composer.js")

    assert "addEventListener(\"sg-" not in source
    assert "appActions.updateSession(" in context_source
    assert "appActions.refreshImage()" in image_source
    assert "appActions.revertImage()" in image_source
    assert "appActions.deleteImage()" in image_source
    assert "appActions.toggleTheme()" in general_source
    assert "appActions.resetNpc()" in general_source
    assert "appActions.toggleSelectorPanel()" in composer_source


def test_sg_input_split_components_use_icon_constants_instead_of_render_functions():
    image_source = _read("engine/web/static/js/sg-input-image.js")
    general_source = _read("engine/web/static/js/sg-input-general.js")
    composer_source = _read("engine/web/static/js/sg-input-composer.js")

    assert "const REFRESH_ICON" in image_source
    assert "const REVERT_ICON" in image_source
    assert "const DELETE_ICON" in image_source
    assert "function renderRefreshIcon" not in image_source
    assert "function renderRevertIcon" not in image_source
    assert "function renderDeleteIcon" not in image_source

    assert "const THEME_DARK_ICON" in general_source
    assert "const THEME_LIGHT_ICON" in general_source
    assert "function renderThemeDarkIcon" not in general_source
    assert "function renderThemeLightIcon" not in general_source

    assert "const SEND_ICON" in composer_source
    assert "const GEAR_ICON" in composer_source
    assert "function renderSendIcon" not in composer_source
    assert "function renderGearIcon" not in composer_source


def test_sg_input_renders_options_trigger_and_panel_actions_in_order():
    source = _read("engine/web/static/js/sg-input.js")

    assert 'id="sg-options-panel"' in source
    assert 'class="sg-options-tabs-list" role="tablist"' in source
    assert 'class="sg-options-tab"' in source
    assert 'class="sg-options-tab-panel"' in source
    assert 'aria-selected="${selected}"' in source
    assert "sg-options-accordion" not in source
    assert "<sg-input-context></sg-input-context>" in source
    assert "<sg-input-image></sg-input-image>" in source
    assert "<sg-input-general></sg-input-general>" in source
    assert "<sg-input-composer></sg-input-composer>" in source

    composer_source = _read("engine/web/static/js/sg-input-composer.js")
    image_source = _read("engine/web/static/js/sg-input-image.js")

    refresh_index = image_source.find('data-action="refresh-image"')
    revert_index = image_source.find('data-action="revert-image"')
    delete_index = image_source.find('data-action="delete-image"')

    assert 'class="sg-options-toggle"' in composer_source
    assert 'aria-controls="sg-options-panel"' in composer_source
    assert 'aria-expanded="false"' in composer_source
    assert "Optionen" in composer_source
    assert refresh_index != -1
    assert revert_index != -1
    assert delete_index != -1
    assert refresh_index < revert_index < delete_index


def test_app_actions_revert_image_uses_confirm_and_revert_endpoint():
    source = _read("engine/web/static/js/app-actions.js")

    assert "async function revertImage()" in source
    assert "window.confirm(" in source
    assert "/api/image/revert-active" in source
    assert "method: \"POST\"" in source


def test_app_actions_delete_image_uses_confirm_and_delete_endpoint():
    source = _read("engine/web/static/js/app-actions.js")

    assert "async function deleteImage()" in source
    assert "window.confirm(" in source
    assert "/api/image/delete-active" in source
    assert "method: \"DELETE\"" in source


def test_confirm_actions_return_execution_status_for_cancel_safe_ui_flow():
    source = _read("engine/web/static/js/app-actions.js")

    assert "async function revertImage()" in source
    assert "async function deleteImage()" in source
    assert "async function resetNpc()" in source
    assert "return false" in source
    assert "return true" in source


def test_confirm_actions_close_selector_panel_only_when_action_executed():
    image_source = _read("engine/web/static/js/sg-input-image.js")
    general_source = _read("engine/web/static/js/sg-input-general.js")

    assert "const hasExecuted = await appActions.revertImage()" in image_source
    assert "const hasExecuted = await appActions.deleteImage()" in image_source
    assert "if (hasExecuted && appStore.getState().isSelectorPanelOpen)" in image_source

    assert "const hasExecuted = await appActions.resetNpc()" in general_source
    assert "if (hasExecuted && appStore.getState().isSelectorPanelOpen)" in general_source


def test_sg_input_subscribes_directly_to_store_keys():
    source = _read("engine/web/static/js/sg-input.js")

    assert 'import { appStore } from "./app-store.js"' in source
    assert '["isSending", this.onIsSendingChanged.bind(this)]' in source
    assert '["isSessionLoading", this.onSessionLoadingChanged.bind(this)]' in source
    assert '["isSelectorPanelOpen", this.onSelectorPanelChanged.bind(this)]' in source
    assert "appStore.subscribe(key, listener)" in source
    assert "setState(nextState = {})" not in source


def test_sg_input_split_components_manage_own_store_subscriptions():
    context_source = _read("engine/web/static/js/sg-input-context.js")
    image_source = _read("engine/web/static/js/sg-input-image.js")
    general_source = _read("engine/web/static/js/sg-input-general.js")
    composer_source = _read("engine/web/static/js/sg-input-composer.js")

    assert 'import { appStore } from "./app-store.js"' in context_source
    assert '["npcs", this.onNpcsChanged.bind(this)]' in context_source
    assert '["scenes", this.onScenesChanged.bind(this)]' in context_source
    assert '["npcId", this.onNpcIdChanged.bind(this)]' in context_source
    assert '["sceneId", this.onSceneIdChanged.bind(this)]' in context_source

    assert 'import { appStore } from "./app-store.js"' in image_source
    assert '["isImageRefreshLoading", this.onDisabledTriggerChanged.bind(this)]' in image_source

    assert 'import { appStore } from "./app-store.js"' in general_source
    assert '["theme", this.onThemeChanged.bind(this)]' in general_source

    assert 'import { appStore } from "./app-store.js"' in composer_source
    assert '["input", this.onInputChanged.bind(this)]' in composer_source
    assert '["isAssistantTyping", this.onIsAssistantTypingChanged.bind(this)]' in composer_source


def test_sg_input_renders_typing_dots_in_composer_meta():
    source = _read("engine/web/static/js/sg-input-composer.js")

    assert "sg-composer-meta" in source
    assert "sg-composer-error sg-hidden" in source
    assert "sg-composer-status" in source
    assert "typing-dots" in source
    assert "Antwort wird geladen" in source
    assert "this._state.isAssistantTyping" in source
    assert "meta.innerHTML" not in source
    assert "this.$.typingStatus.classList.toggle(\"sg-hidden\"" in source
    assert "this.$.keyboardHint.classList.toggle(\"sg-hidden\"" in source


def test_sg_app_renders_scene_thumbnail_markup_directly_and_subscribes_image_url():
    source = _read("engine/web/static/js/sg-app.js")

    assert "sg-scene-image" not in source
    assert '<section class="sg-scene-image-slot" aria-label="Szenenbild">' in source
    assert '<div class="sg-image-empty sg-hidden">Kein Bild geladen</div>' in source
    assert '<sg-thumbnail class="sg-scene-thumbnail"></sg-thumbnail>' in source
    assert 'appStore.subscribe("imageUrl", this.onImageUrlChanged.bind(this))' in source
    assert "renderSceneImageState()" in source


def test_sg_thumbnail_subscribes_directly_to_image_store_keys_and_actions():
    source = _read("engine/web/static/js/sg-thumbnail.js")

    assert 'import { appStore } from "./app-store.js"' in source
    assert 'import { appActions } from "./app-actions.js"' in source
    assert '["imageUrl", this.onImageUrlChanged.bind(this)]' in source
    assert '["isImageExpanded", this.onImageExpandedChanged.bind(this)]' in source
    assert '["isImageRefreshLoading", this.onImageRefreshLoadingChanged.bind(this)]' in source
    assert "appStore.subscribe(key, listener)" in source
    assert "appActions.toggleImageExpand(true)" in source
    assert "appActions.toggleImageExpand(false)" in source
    assert "appActions.setImageError()" in source
    assert "this.closest(\".sg-scene-image-slot\")" not in source
    assert 'const isSceneThumbnail = this.classList.contains("sg-scene-thumbnail")' in source


def test_sg_app_is_thin_orchestrator_for_layout_initial_load_and_focus():
    source = _read("engine/web/static/js/sg-app.js")

    assert "loadInitialState()" in source
    assert 'appStore.subscribe("focusRequestedAt", this.onInputFocusRequested.bind(this))' in source
    assert 'this.$ = {\n      input: this.querySelector("sg-input"),' in source
    assert "this.$.input?.focusInput()" in source
    assert "onImageExpandedChanged(" not in source
    assert "onInputChanged(" not in source
    assert "onThemeChanged(" not in source


def test_sg_app_syncs_app_viewport_height_with_visual_viewport():
    source = _read("engine/web/static/js/sg-app.js")

    assert "registerViewportSync()" in source
    assert "syncViewportHeight()" in source
    assert "window.visualViewport" in source
    assert 'setProperty("--app-vh"' in source


def test_mobile_css_uses_fixed_app_shell_with_app_vh_and_local_composer_anchor():
    source = _read("engine/web/static/css/app.css")

    assert ".app-viewport {" in source
    assert "position: fixed;" in source
    assert "grid-template-rows: minmax(0, 1fr) 0;" in source
    assert "height: var(--app-vh);" in source
    assert "min-height: var(--app-vh);" in source
    assert "overscroll-behavior: none;" in source
    assert "transition: height 180ms ease-out, min-height 180ms ease-out;" in source
    assert ".sg-input-component {" in source
    assert "position: absolute;" in source
    assert "calc(var(--app-vh) * 0.25)" in source
    assert "transition: height 180ms ease-out;" in source


def test_app_actions_dispatches_loading_flags_for_session_and_image_refresh():
    source = _read("engine/web/static/js/app-actions.js")

    assert "appStore.setState({ isSessionLoading: true })" in source
    assert "appStore.setState({ isSessionLoading: false })" in source
    assert "appStore.setState({ isImageRefreshLoading: true })" in source
    assert "appStore.setState({ isImageRefreshLoading: false })" in source


def test_app_actions_toggles_assistant_typing_between_send_start_and_end():
    source = _read("engine/web/static/js/app-actions.js")

    assert "isAssistantTyping: true" in source
    assert "isAssistantTyping: false" in source


def test_submit_message_inserts_assistant_message_only_after_first_chunk():
    source = _read("engine/web/static/js/app-actions.js")

    assert "const assistantTimestamp = createNowTimestamp()" in source
    assert "await streamAssistantReply(text, assistantId, assistantTimestamp)" in source
    assert "messages.push({ id: assistantId, role: \"assistant\"" not in source


def test_sg_app_maps_image_state_keys_to_image_component():
    source = _read("engine/web/static/js/sg-app.js")

    assert "onImageUrlChanged(" in source
    assert "onImageRefreshLoadingChanged(" in source
    assert "onImageExpandedChanged(" not in source
    assert 'appStore.subscribe("imageUrl", this.onImageUrlChanged.bind(this))' in source
    assert 'appStore.subscribe("isImageRefreshLoading", this.onImageRefreshLoadingChanged.bind(this))' in source
    assert "renderSceneImageState()" in source
    assert 'this.$.imageSlot.classList.toggle("is-loading", showSlotLoading)' in source
    assert "setState({ isExpanded" not in source


def test_sg_app_registers_store_subscriptions_via_loop_without_cleanup_wrapper():
    source = _read("engine/web/static/js/sg-app.js")

    assert "const subscriptions = [" not in source
    assert "for (const [action, listener] of subscriptions)" not in source
    assert 'appStore.subscribe("focusRequestedAt", this.onInputFocusRequested.bind(this))' in source
    assert 'appStore.subscribe("imageUrl", this.onImageUrlChanged.bind(this))' in source
    assert 'appStore.subscribe("isImageRefreshLoading", this.onImageRefreshLoadingChanged.bind(this))' in source
    assert "cleanupSubscriptions(" not in source
    assert "_cleanupCallbacks" not in source


def test_app_actions_uses_direct_initial_load_and_polling_without_init_wrapper():
    source = _read("engine/web/static/js/app-actions.js")

    assert "async function loadInitialState()" in source
    assert "export async function loadInitialState()" not in source
    assert "setInterval(() => {" in source
    assert "pollImageSignature()" in source
    assert "initializeAppActions" not in source
    assert "isAppActionsInitialized" not in source


def test_context_gallery_ignores_click_on_current_selection():
    source = _read("engine/web/static/js/sg-context-gallery.js")

    assert "const selectedId = typeof state[this._stateKey] === \"string\" ? state[this._stateKey] : \"\"" in source
    assert "if (itemId === selectedId) return" in source

