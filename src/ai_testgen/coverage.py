"""Traceability: which generated tests cover which acceptance criteria and API responses."""

from __future__ import annotations

from collections import Counter
from typing import Any

from ai_testgen.models import Endpoint, TestCase, UserStory


def _ratio(covered: int, total: int) -> float:
    return round(covered / total, 4) if total else 1.0


def coverage_map(
    cases: list[TestCase], stories: list[UserStory], endpoints: list[Endpoint]
) -> dict[str, Any]:
    by_trace: dict[str, list[str]] = {}
    for case in cases:
        for trace in case.traces:
            by_trace.setdefault(trace, []).append(case.id)

    criteria = {ac.id: by_trace.get(ac.id, []) for s in stories for ac in s.criteria}
    operations = {e.id: by_trace.get(e.id, []) for e in endpoints}
    responses = {rid: by_trace.get(rid, []) for e in endpoints for rid in e.response_ids()}

    return {
        "acceptance_criteria": criteria,
        "endpoints": operations,
        "responses": responses,
        "summary": {
            "ac_coverage": _ratio(sum(bool(v) for v in criteria.values()), len(criteria)),
            "endpoint_coverage": _ratio(sum(bool(v) for v in operations.values()), len(operations)),
            "response_coverage": _ratio(sum(bool(v) for v in responses.values()), len(responses)),
            "uncovered": sorted(
                k for k, v in {**criteria, **operations, **responses}.items() if not v
            ),
            "by_type": dict(sorted(Counter(c.type for c in cases).items())),
        },
    }
