from __future__ import annotations

from collections import Counter

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from engine.api.app import app


def _operation_ids() -> list[str]:
    spec = app.openapi()
    operation_ids: list[str] = []
    for path_item in spec.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict) and "operationId" in operation:
                operation_ids.append(operation["operationId"])
    return operation_ids


def test_openapi_uses_unique_camel_case_operation_ids_from_function_names() -> None:
    operation_ids = _operation_ids()
    counts = Counter(operation_ids)

    assert len(operation_ids) == len(counts)
    assert "chatStream" in counts
    assert "npcCreate" in counts
    assert "imageCurrent" in counts
    assert "imageDescribeNpc" in counts
    assert "imagePreviewNpc" in counts
    assert "npcResetActive" in counts


def test_openapi_and_docs_endpoints_are_available() -> None:
    with TestClient(app) as client:
        assert client.get("/openapi.json").status_code == 200
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200


def test_routes_define_readable_manual_operation_ids() -> None:
    api_routes = [route for route in app.routes if isinstance(route, APIRoute)]

    assert api_routes
    assert all(route.operation_id for route in api_routes)


def test_openapi_error_response_type_is_plain_string() -> None:
    spec = app.openapi()
    schemas = spec.get("components", {}).get("schemas", {})
    error_response = schemas.get("ErrorResponse", {})
    error_type = error_response.get("properties", {}).get("type", {})

    assert error_type.get("type") == "string"
    assert "$ref" not in error_type
    assert "enum" not in error_type
