"""JSON Schema for generated test cases, plus checks a schema can't express.

Model output is untrusted input. Every case is validated before it reaches code generation;
invalid cases are dropped and reported rather than silently patched.
"""

from __future__ import annotations

import re
from typing import Any

from jsonschema import Draft202012Validator

from ai_testgen.models import CASE_TYPES, PRIORITIES

_STRINGS = {"type": "array", "items": {"type": "string", "minLength": 1}}

CASE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["title", "type", "priority", "steps", "expected", "traces"],
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string", "minLength": 5, "maxLength": 200},
        "type": {"enum": list(CASE_TYPES)},
        "priority": {"enum": list(PRIORITIES)},
        "preconditions": _STRINGS,
        "steps": {**_STRINGS, "minItems": 1},
        "expected": {"type": "string", "minLength": 3},
        "traces": {**_STRINGS, "minItems": 1},
        "tags": _STRINGS,
        "request": {
            "type": "object",
            "required": ["method", "path"],
            "additionalProperties": False,
            "properties": {
                "method": {"enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]},
                "path": {"type": "string", "pattern": "^/"},
                "path_params": {"type": "object"},
                "query": {"type": "object"},
                "body": {},
                "auth": {"enum": ["valid", "none", "invalid"]},
            },
        },
        "expect": {
            "type": "object",
            "additionalProperties": False,
            "anyOf": [{"required": ["status"]}, {"required": ["status_in"]}],
            "properties": {
                "status": {"type": "integer", "minimum": 100, "maximum": 599},
                "status_in": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "integer", "minimum": 100, "maximum": 599},
                },
                "body_keys": _STRINGS,
                "body_type": {"enum": ["array", "object"]},
            },
        },
    },
}

_VALIDATOR = Draft202012Validator(CASE_SCHEMA)
_PLACEHOLDER_RE = re.compile(r"\{([^}]+)\}")


def schema_errors(case: Any) -> list[str]:
    if not isinstance(case, dict):
        return ["test case is not a JSON object"]
    errors = []
    for error in sorted(_VALIDATOR.iter_errors(case), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"{where}: {error.message}")
    return errors


def validate_story_case(case: Any, criteria_ids: set[str]) -> list[str]:
    errors = schema_errors(case)
    if errors:
        return errors
    unknown = [t for t in case["traces"] if t not in criteria_ids]
    if unknown:
        errors.append(f"traces reference unknown acceptance criteria: {unknown}")
    return errors


def validate_api_case(case: Any, endpoint: dict[str, Any]) -> list[str]:
    errors = schema_errors(case)
    if errors:
        return errors
    if "request" not in case or "expect" not in case:
        return ["API test cases need 'request' and 'expect'"]
    request = case["request"]
    if request["method"] != endpoint["method"] or request["path"] != endpoint["path"]:
        errors.append(
            f"request targets {request['method']} {request['path']}, expected {endpoint['id']}"
        )
    missing = set(_PLACEHOLDER_RE.findall(endpoint["path"])) - set(request.get("path_params") or {})
    if missing:
        errors.append(f"missing path parameters: {sorted(missing)}")
    documented = {int(code) for code in endpoint["responses"]}
    expected = case["expect"].get("status_in") or [case["expect"].get("status")]
    undocumented = sorted(set(expected) - documented)
    if undocumented:
        errors.append(f"expects undocumented status codes {undocumented}")
    return errors
