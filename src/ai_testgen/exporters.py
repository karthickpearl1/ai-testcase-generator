"""Export test cases for test management tools and humans.

The Xray and Zephyr outputs follow the shape of those tools' JSON import formats (Xray's
test import and Zephyr Scale's test case API). Field mappings differ between instances, so
treat them as a starting point to adjust rather than a guaranteed one-click import.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from ai_testgen.models import TestCase

_PRIORITY_NAMES = {"high": "High", "medium": "Medium", "low": "Low"}


def _request_data(case: TestCase) -> str:
    if case.request is None:
        return ""
    return json.dumps({k: v for k, v in case.request.items() if v not in (None, {}, "none")})


def to_csv(cases: list[TestCase]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        [
            "id",
            "title",
            "type",
            "priority",
            "source",
            "traces",
            "preconditions",
            "steps",
            "expected",
            "test_data",
        ]
    )
    for c in cases:
        writer.writerow(
            [
                c.id,
                c.title,
                c.type,
                c.priority,
                c.source_ref,
                "; ".join(c.traces),
                "\n".join(c.preconditions),
                "\n".join(f"{i}. {s}" for i, s in enumerate(c.steps, 1)),
                c.expected,
                _request_data(c),
            ]
        )
    return buffer.getvalue()


def _md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", "<br>")


def to_markdown(cases: list[TestCase]) -> str:
    lines = ["# Generated test cases", ""]
    sources: dict[str, list[TestCase]] = {}
    for case in cases:
        sources.setdefault(case.source_ref, []).append(case)
    for source, group in sources.items():
        lines += [
            f"## {source}",
            "",
            "| ID | Type | Priority | Title | Steps | Expected | Traces |",
            "|---|---|---|---|---|---|---|",
        ]
        for c in group:
            steps = "<br>".join(f"{i}. {_md(s)}" for i, s in enumerate(c.steps, 1))
            lines.append(
                f"| {c.id} | {c.type} | {c.priority} | {_md(c.title)} | {steps} | "
                f"{_md(c.expected)} | {', '.join(c.traces)} |"
            )
        lines.append("")
    return "\n".join(lines)


def _steps(case: TestCase) -> list[tuple[str, str, str]]:
    """(action, data, result) triples; the expected result belongs to the last step."""
    data = _request_data(case)
    rows = [(step, data if i == 0 else "", "") for i, step in enumerate(case.steps)]
    action, step_data, _ = rows[-1]
    rows[-1] = (action, step_data, case.expected)
    return rows


def to_xray(cases: list[TestCase], project_key: str) -> list[dict[str, Any]]:
    return [
        {
            "testtype": "Manual",
            "fields": {
                "summary": f"{c.id}: {c.title}",
                "project": {"key": project_key},
                "priority": {"name": _PRIORITY_NAMES[c.priority]},
                "labels": sorted({c.type, *[t.replace(" ", "_") for t in c.tags]}),
                "description": "Preconditions:\n"
                + ("\n".join(f"- {p}" for p in c.preconditions) or "- none")
                + f"\n\nTraces: {', '.join(c.traces)}",
            },
            "steps": [{"action": a, "data": d, "result": r} for a, d, r in _steps(c)],
        }
        for c in cases
    ]


def to_zephyr(cases: list[TestCase], project_key: str) -> list[dict[str, Any]]:
    return [
        {
            "projectKey": project_key,
            "name": f"{c.id}: {c.title}",
            "objective": f"Verify {', '.join(c.traces)}",
            "precondition": "\n".join(c.preconditions),
            "priorityName": _PRIORITY_NAMES[c.priority],
            "labels": sorted({c.type, *[t.replace(" ", "_") for t in c.tags]}),
            "testScript": {
                "type": "STEP_BY_STEP",
                "steps": [
                    {"description": a, "testData": d, "expectedResult": r} for a, d, r in _steps(c)
                ],
            },
        }
        for c in cases
    ]
