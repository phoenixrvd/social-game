from __future__ import annotations

import openai
import requests

from engine.llm.provider_client import normalize_provider_error_detail, user_visible_provider_error_detail


def _runtime_error_from_openai(detail: str) -> RuntimeError:
    try:
        raise openai.OpenAIError("upstream")
    except openai.OpenAIError as cause:
        try:
            raise RuntimeError(detail) from cause
        except RuntimeError as exc:
            return exc


def test_normalize_provider_error_detail_extracts_and_trims_payload_message():
    detail = (
        "PermissionDeniedError(\"Error code: 403 - {'code': 'forbidden', 'error': 'Content violates usage "
        "guidelines. Team: abc Failed check: SAFETY_CHECK_TYPE_CSAM'}\")"
    )
    assert normalize_provider_error_detail(detail) == "Content violates usage guidelines."


def test_normalize_provider_error_detail_reads_json_payload_from_embedded_text():
    detail = (
        'PermissionDeniedError("Error code: 403 - {"code": "forbidden", "error": '
        '"Content violates usage guidelines. Team: abc Failed check: SAFETY_CHECK_TYPE_CSAM"} '
        'Request ID: req-123")'
    )
    assert normalize_provider_error_detail(detail) == "Content violates usage guidelines."


def test_user_visible_provider_error_detail_prefers_wrapped_runtime_message():
    exc = _runtime_error_from_openai("Anfrage durch Moderation blockiert.")
    assert user_visible_provider_error_detail(exc) == "Anfrage durch Moderation blockiert."


def test_user_visible_provider_error_detail_uses_direct_provider_message_when_needed():
    class FakePermissionDenied(openai.OpenAIError):
        pass

    exc = FakePermissionDenied(
        "PermissionDeniedError(\"Error code: 403 - {'code': 'forbidden', 'error': 'Content violates usage "
        "guidelines. Team: abc Failed check: SAFETY_CHECK_TYPE_CSAM'}\")"
    )
    assert user_visible_provider_error_detail(exc) == "Content violates usage guidelines."


def test_user_visible_provider_error_detail_detects_wrapped_request_errors():
    response = requests.Response()
    response.status_code = 404
    response.url = "https://imgen.x.ai/moderated_content.png"
    cause = requests.HTTPError("404 Not Found", response=response)
    try:
        raise cause
    except requests.HTTPError as exc:
        try:
            raise RuntimeError("Anfrage durch Moderation blockiert.") from exc
        except RuntimeError as wrapped:
            assert user_visible_provider_error_detail(wrapped) == "Anfrage durch Moderation blockiert."


def test_user_visible_provider_error_detail_returns_none_without_provider_cause():
    assert user_visible_provider_error_detail(RuntimeError("internal")) is None
