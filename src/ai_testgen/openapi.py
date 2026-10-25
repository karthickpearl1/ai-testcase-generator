"""Load an OpenAPI 3 document into a flat list of endpoints with local $refs resolved."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml

from ai_testgen.models import Endpoint, Parameter

HTTP_METHODS = ("get", "post", "put", "patch", "delete")


def _resolve(node: Any, root: dict[str, Any], seen: tuple[str, ...] = ()) -> Any:
    """Recursively inline local ``#/...`` references. Remote refs are not supported."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if ref is not None:
            if not ref.startswith("#/"):
                raise ValueError(f"Only local $refs are supported, got {ref}")
            if ref in seen:
                raise ValueError(f"Circular $ref: {ref}")
            target: Any = root
            for part in ref[2:].split("/"):
                target = target[part]
            return _resolve(copy.deepcopy(target), root, (*seen, ref))
        return {k: _resolve(v, root, seen) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve(v, root, seen) for v in node]
    return node


def _json_schema(content: dict[str, Any] | None) -> dict[str, Any] | None:
    if not content:
        return None
    media = content.get("application/json") or next(iter(content.values()), {})
    return media.get("schema")


def load_openapi(path: str | Path) -> list[Endpoint]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    raw = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    if not isinstance(raw, dict) or not str(raw.get("openapi", "")).startswith("3."):
        raise ValueError(f"{path} is not an OpenAPI 3 document")
    spec = _resolve(raw, raw)
    global_security = bool(spec.get("security"))

    endpoints: list[Endpoint] = []
    for route, item in (spec.get("paths") or {}).items():
        shared = {(p["name"], p["in"]): p for p in item.get("parameters", [])}
        for method in HTTP_METHODS:
            operation = item.get(method)
            if operation is None:
                continue
            # Operation-level parameters override path-level ones with the same name/location.
            merged = dict(shared)
            merged.update({(p["name"], p["in"]): p for p in operation.get("parameters", [])})
            parameters = tuple(
                Parameter(p["name"], p["in"], bool(p.get("required")), p.get("schema", {}))
                for p in merged.values()
            )
            responses = {
                int(code): _json_schema(resp.get("content"))
                for code, resp in operation.get("responses", {}).items()
                if str(code).isdigit()
            }
            security = operation.get("security")
            endpoints.append(
                Endpoint(
                    method=method.upper(),
                    path=route,
                    operation_id=operation.get("operationId", f"{method}_{route}"),
                    summary=operation.get("summary", ""),
                    parameters=parameters,
                    request_schema=_json_schema(
                        (operation.get("requestBody") or {}).get("content")
                    ),
                    responses=responses,
                    requires_auth=bool(security) if security is not None else global_security,
                )
            )
    if not endpoints:
        raise ValueError(f"No operations found in {path}")
    return endpoints
