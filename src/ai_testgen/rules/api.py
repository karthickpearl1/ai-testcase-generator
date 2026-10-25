"""Test design rules for a single OpenAPI operation.

Input and output are plain dicts in exactly the shape the generation prompt asks an LLM to
return, so the mock model and a real model are interchangeable downstream.
"""

from __future__ import annotations

import copy
from typing import Any

NOT_FOUND_ID = 999999
INJECTION_PAYLOAD = "Robert'); DROP TABLE books;--"
VALIDATION_CODES = (400, 422)


def example_for(schema: dict[str, Any]) -> Any:
    """A valid example value for a schema: explicit example, enum member, or derived."""
    if "example" in schema:
        return schema["example"]
    if schema.get("enum"):
        return schema["enum"][0]
    kind = schema.get("type")
    if kind == "string":
        return "x" * max(int(schema.get("minLength", 1)), 1)
    if kind == "integer":
        return int(schema.get("minimum", 1))
    if kind == "number":
        return float(schema.get("minimum", 1.0))
    if kind == "boolean":
        return True
    if kind == "array":
        return []
    if kind == "object":
        return build_body(schema)
    return None


def build_body(schema: dict[str, Any]) -> dict[str, Any]:
    """A valid body: required properties plus optional ones that have an example."""
    required = set(schema.get("required", []))
    return {
        name: example_for(prop)
        for name, prop in schema.get("properties", {}).items()
        if name in required or "example" in prop
    }


def _wrong_type_value(schema: dict[str, Any]) -> Any:
    return 12345 if schema.get("type") == "string" else "not-a-number"


def _limits(schema: dict[str, Any]) -> list[tuple[str, Any, Any, bool]]:
    """Boundary probes as (label, value, limit, valid) for string length and numeric range."""
    kind = schema.get("type")
    probes: list[tuple[str, Any, Any, bool]] = []
    if kind == "string":
        if "minLength" in schema:
            low = int(schema["minLength"])
            probes.append(("at minimum length", "x" * low, low, True))
            if low > 0:
                probes.append(("below minimum length", "x" * (low - 1), low, False))
        if "maxLength" in schema:
            high = int(schema["maxLength"])
            probes.append(("at maximum length", "x" * high, high, True))
            probes.append(("above maximum length", "x" * (high + 1), high, False))
    elif kind in {"integer", "number"}:
        step = 1 if kind == "integer" else 0.01
        if "minimum" in schema:
            low = schema["minimum"]
            probes.append(("at minimum", low, low, True))
            probes.append(("below minimum", round(low - step, 2), low, False))
        if "maximum" in schema:
            high = schema["maximum"]
            probes.append(("at maximum", high, high, True))
            probes.append(("above maximum", round(high + step, 2), high, False))
    return probes


class _Builder:
    def __init__(self, endpoint: dict[str, Any]) -> None:
        self.ep = endpoint
        self.codes = sorted(int(c) for c in endpoint["responses"])
        self.success = next((c for c in self.codes if 200 <= c < 300), self.codes[0])
        self.validation = next((c for c in self.codes if c in VALIDATION_CODES), None)
        self.params = endpoint.get("parameters", [])
        self.body_schema = endpoint.get("request_schema")
        self.cases: list[dict[str, Any]] = []
        self.label = endpoint.get("summary") or endpoint["id"]

    # -- request helpers -------------------------------------------------------------------
    def base_request(self) -> dict[str, Any]:
        return {
            "method": self.ep["method"],
            "path": self.ep["path"],
            "path_params": {
                p["name"]: example_for(p["schema"]) for p in self.params if p["location"] == "path"
            },
            "query": {
                p["name"]: example_for(p["schema"])
                for p in self.params
                if p["location"] == "query" and p["required"]
            },
            "body": build_body(self.body_schema) if self.body_schema else None,
            "auth": "valid" if self.ep["requires_auth"] else "none",
        }

    def success_expect(self) -> dict[str, Any]:
        expect: dict[str, Any] = {"status": self.success}
        schema = self.ep["responses"].get(str(self.success)) or {}
        if schema.get("type") == "array":
            expect["body_type"] = "array"
        elif schema.get("required"):
            expect["body_keys"] = list(schema["required"])
        return expect

    def add(
        self,
        title: str,
        case_type: str,
        request: dict[str, Any],
        expect: dict[str, Any],
        steps_note: str,
        priority: str = "medium",
    ) -> None:
        status = expect.get("status", expect.get("status_in"))
        trace_codes = [status] if isinstance(status, int) else status
        self.cases.append(
            {
                "title": title,
                "type": case_type,
                "priority": priority,
                "preconditions": ["A valid bearer token is available"]
                if request["auth"] == "valid"
                else [],
                "steps": [f"Send {request['method']} {request['path']} {steps_note}".strip()],
                "expected": f"Response status is {status}"
                if isinstance(status, int)
                else f"Response status is one of {status} (never a server error)",
                "traces": [self.ep["id"]]
                + [f"{self.ep['id']} {c}" for c in trace_codes if str(c) in self.ep["responses"]],
                "tags": ["api", case_type],
                "request": request,
                "expect": expect,
            }
        )

    # -- design techniques -----------------------------------------------------------------
    def positive(self) -> None:
        self.add(
            f"{self.label} succeeds with valid input",
            "positive",
            self.base_request(),
            self.success_expect(),
            "with valid parameters and body",
            "high",
        )

    def parameter_cases(self) -> None:
        for param in self.params:
            schema, name = param["schema"], param["name"]
            if (
                param["location"] == "path"
                and 404 in self.codes
                and schema.get("type") == "integer"
            ):
                request = self.base_request()
                request["path_params"][name] = NOT_FOUND_ID
                self.add(
                    f"{self.label} returns 404 for a non-existent {name}",
                    "negative",
                    request,
                    {"status": 404},
                    f"with {name}={NOT_FOUND_ID}",
                )
            if param["location"] != "query":
                continue
            for label, value, limit, valid in _limits(schema):
                if not valid and self.validation is None:
                    continue
                request = self.base_request()
                request["query"][name] = value
                expect = self.success_expect() if valid else {"status": self.validation}
                outcome = "is accepted" if valid else "is rejected"
                self.add(
                    f"{self.label}: query {name} {label} ({limit}) {outcome}",
                    "boundary",
                    request,
                    expect,
                    f"with {name}={value}",
                )

    def body_cases(self) -> None:
        schema = self.body_schema
        if not schema:
            return
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        if self.validation is not None:
            for name in required:
                request = self.base_request()
                del request["body"][name]
                self.add(
                    f"{self.label} is rejected when required field '{name}' is missing",
                    "negative",
                    request,
                    {"status": self.validation},
                    f"without '{name}' in the body",
                )
                request = self.base_request()
                request["body"][name] = _wrong_type_value(properties[name])
                self.add(
                    f"{self.label} is rejected when '{name}' has the wrong type",
                    "negative",
                    request,
                    {"status": self.validation},
                    f"with a {type(request['body'][name]).__name__} for '{name}'",
                )
            for name, prop in properties.items():
                if prop.get("enum"):
                    request = self.base_request()
                    request["body"][name] = "not-a-valid-option"
                    self.add(
                        f"{self.label} is rejected when '{name}' is not an allowed value",
                        "negative",
                        request,
                        {"status": self.validation},
                        f"with an unknown '{name}'",
                    )

        for name, prop in properties.items():
            for label, value, limit, valid in _limits(prop):
                if not valid and self.validation is None:
                    continue
                request = self.base_request()
                request["body"][name] = value
                expect = self.success_expect() if valid else {"status": self.validation}
                outcome = "is accepted" if valid else "is rejected"
                self.add(
                    f"{self.label}: '{name}' {label} ({limit}) {outcome}",
                    "boundary",
                    request,
                    expect,
                    f"with '{name}' {label}",
                )

        if 404 in self.codes:
            for name, prop in properties.items():
                if name.endswith("_id") and prop.get("type") == "integer":
                    request = self.base_request()
                    request["body"][name] = NOT_FOUND_ID
                    self.add(
                        f"{self.label} returns 404 when '{name}' does not exist",
                        "negative",
                        request,
                        {"status": 404},
                        f"with '{name}'={NOT_FOUND_ID}",
                    )

    def security_cases(self) -> None:
        if self.ep["requires_auth"] and 401 in self.codes:
            for auth, wording in (
                ("none", "without a token"),
                ("invalid", "with an invalid token"),
            ):
                request = self.base_request()
                request["auth"] = auth
                self.add(
                    f"{self.label} is refused {wording}",
                    "security",
                    request,
                    {"status": 401},
                    wording,
                    "high",
                )
        properties = (self.body_schema or {}).get("properties", {})
        target = next(
            (
                n
                for n, p in properties.items()
                if p.get("type") == "string"
                and not p.get("enum")
                and int(p.get("maxLength", 1000)) >= len(INJECTION_PAYLOAD)
            ),
            None,
        )
        if target and self.validation is not None:
            request = self.base_request()
            request["body"][target] = INJECTION_PAYLOAD
            self.add(
                f"{self.label} handles an injection payload in '{target}' without a server error",
                "security",
                request,
                {"status_in": [self.success, self.validation]},
                f"with an SQL injection string in '{target}'",
                "high",
            )


def cases_for_endpoint(endpoint: dict[str, Any]) -> list[dict[str, Any]]:
    builder = _Builder(copy.deepcopy(endpoint))
    builder.positive()
    builder.parameter_cases()
    builder.body_cases()
    builder.security_cases()
    return builder.cases
