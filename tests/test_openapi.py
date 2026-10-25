import json

import pytest

from ai_testgen.openapi import load_openapi


def test_endpoints_are_flattened_and_resolved(endpoints):
    ids = [e.id for e in endpoints]
    assert ids == [
        "GET /health",
        "GET /books",
        "POST /books",
        "GET /books/{bookId}",
        "DELETE /books/{bookId}",
        "POST /orders",
    ]
    create = endpoints[2]
    assert create.requires_auth
    assert create.request_schema["required"] == ["title", "author", "price"]
    assert create.responses[201]["properties"]["format"]["enum"] == [
        "hardback",
        "paperback",
        "ebook",
    ]
    assert create.responses[400]["required"] == ["error"]
    assert create.response_ids() == ["POST /books 201", "POST /books 400", "POST /books 401"]


def test_operation_parameters_override_path_parameters(endpoints):
    get_book, delete_book = endpoints[3], endpoints[4]
    assert get_book.parameters[0].schema["example"] == 1
    assert delete_book.parameters[0].schema["example"] == 2
    assert not get_book.requires_auth


def _write(tmp_path, spec, suffix=".json"):
    path = tmp_path / f"spec{suffix}"
    path.write_text(json.dumps(spec))
    return path


def test_global_security_and_json_specs(tmp_path):
    spec = {
        "openapi": "3.1.0",
        "security": [{"key": []}],
        "paths": {"/x": {"get": {"responses": {"200": {"description": "ok"}, "default": {}}}}},
    }
    (endpoint,) = load_openapi(_write(tmp_path, spec))
    assert endpoint.requires_auth
    assert endpoint.responses == {200: None}
    assert endpoint.operation_id == "get_/x"


@pytest.mark.parametrize(
    ("spec", "message"),
    [
        ({"swagger": "2.0"}, "not an OpenAPI 3"),
        ({"openapi": "3.0.0", "paths": {}}, "No operations"),
        ({"openapi": "3.0.0", "paths": {"/x": {"$ref": "other.yaml#/x"}}}, "Only local"),
        ({"openapi": "3.0.0", "a": {"$ref": "#/b"}, "b": {"$ref": "#/a"}}, "Circular"),
    ],
)
def test_invalid_specs(tmp_path, spec, message):
    with pytest.raises(ValueError, match=message):
        load_openapi(_write(tmp_path, spec))
