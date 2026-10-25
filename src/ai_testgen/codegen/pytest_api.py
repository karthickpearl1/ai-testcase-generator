"""Render API test cases as a self-contained pytest suite."""

from __future__ import annotations

import json
import re
from importlib import resources
from pathlib import Path
from typing import Any

from ai_testgen.models import Endpoint, TestCase

_PYTEST_INI = """[pytest]
markers =
    positive: happy-path behaviour
    negative: invalid input and error handling
    boundary: limits of constrained values
    security: authentication and injection handling
"""


def py_literal(value: Any) -> str:
    """Render JSON-like data as a compact Python literal.

    Long strings made of one repeated character (boundary values such as 121 'x's) are
    written as ``"x" * 121`` so the generated test stays readable.
    """
    if isinstance(value, str):
        if len(value) > 12 and len(set(value)) == 1:
            return f'"{value[0]}" * {len(value)}'
        return json.dumps(value, ensure_ascii=False)  # JSON string escapes are valid Python
    if isinstance(value, bool) or value is None:
        return repr(value)
    if isinstance(value, int | float):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(py_literal(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{py_literal(k)}: {py_literal(v)}" for k, v in value.items()) + "}"
    raise TypeError(f"Cannot render {type(value).__name__} as a literal")


def slug(text: str, limit: int = 48) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    out = ""
    for word in words:
        candidate = f"{out}_{word}" if out else word
        if len(candidate) > limit:
            break
        out = candidate
    return out or "case"


def function_name(case: TestCase, prefix: str = "") -> str:
    """``test_tc_007_<slug>``; ``prefix`` (the endpoint summary) is dropped from the slug."""
    title = case.title
    if prefix and title.lower().startswith(prefix.lower()):
        title = title[len(prefix) :].lstrip(" :")
    return f"test_{case.id.lower().replace('-', '_')}_{slug(title)}"


def _tuple(items: list[str]) -> str:
    return f"({items[0]},)" if len(items) == 1 else f"({', '.join(items)})"


def _argument(name: str, value: Any) -> list[str]:
    """A keyword argument, split over several lines when a dict would be too long."""
    literal = py_literal(value)
    if not isinstance(value, dict) or len(literal) <= 70:
        return [f"        {name}={literal},"]
    return [
        f"        {name}={{",
        *[f"            {py_literal(k)}: {py_literal(v)}," for k, v in value.items()],
        "        },",
    ]


def render_test(case: TestCase, prefix: str = "") -> str:
    request, expect = case.request or {}, case.expect or {}
    args = [f"        {py_literal(request['method'])},", f"        {py_literal(request['path'])},"]
    for key in ("path_params", "query"):
        if request.get(key):
            args += _argument(key, request[key])
    if request.get("body") is not None:
        args += _argument("body", request["body"])
    if request.get("auth", "none") != "none":
        args.append(f"        auth={py_literal(request['auth'])},")

    lines = [
        f"@pytest.mark.{case.type}",
        f"def {function_name(case, prefix)}(api):",
        f'    """{case.id}: {case.title.replace(chr(34) * 3, "")}',
        "",
        f"    Traces: {', '.join(case.traces)}",
        '    """',
        "    response = api.request(",
        *args,
        "    )",
    ]
    if "status" in expect:
        lines.append(f"    assert response.status_code == {expect['status']}, response.text")
    else:
        codes = _tuple([str(c) for c in expect["status_in"]])
        lines.append(f"    assert response.status_code in {codes}, response.text")
    if expect.get("body_type") == "array":
        lines.append("    assert isinstance(response.json(), list)")
    if expect.get("body_keys"):
        keys = _tuple([py_literal(k) for k in expect["body_keys"]])
        lines += [
            "    body = response.json()",
            f"    for key in {keys}:",
            '        assert key in body, f"response is missing {key!r}"',
        ]
    return "\n".join(lines)


def render_module(endpoint: Endpoint, cases: list[TestCase], spec_name: str) -> str:
    header = [
        f'"""Generated API tests for {endpoint.id} ({endpoint.summary or endpoint.operation_id}).',
        "",
        f"Source: {spec_name}. Regenerate with `testgen generate` rather than editing by hand.",
        '"""',
        "",
        "import pytest",
        "",
    ]
    prefix = endpoint.summary or ""
    body = "\n\n\n".join(render_test(c, prefix) for c in cases)
    return "\n".join(header) + "\n\n" + body + "\n"


def write_pytest_suite(
    cases: list[TestCase], endpoints: list[Endpoint], out_dir: Path, spec_name: str
) -> list[Path]:
    """Write conftest.py, pytest.ini and one test module per endpoint; return module paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    conftest = resources.files("ai_testgen.codegen").joinpath("templates/conftest.py.txt")
    (out_dir / "conftest.py").write_text(conftest.read_text(encoding="utf-8"), encoding="utf-8")
    (out_dir / "pytest.ini").write_text(_PYTEST_INI, encoding="utf-8")

    written = []
    for endpoint in endpoints:
        selected = [c for c in cases if c.request is not None and c.source_ref == endpoint.id]
        if not selected:
            continue
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", endpoint.operation_id).lower()
        path = out_dir / f"test_{slug(name, 40)}.py"
        path.write_text(render_module(endpoint, selected, spec_name), encoding="utf-8")
        written.append(path)
    return written
