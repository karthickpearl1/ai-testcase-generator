"""Remove duplicate test cases, keeping the first and merging traceability."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ai_testgen.models import TestCase

_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Duplicate:
    dropped: str
    kept: str
    reason: str


def _words(text: str) -> frozenset[str]:
    return frozenset(_WORD_RE.findall(text.lower()))


def signature(case: TestCase) -> str:
    """Exact identity: for API cases the request and expectation, otherwise the wording."""
    if case.request is not None:
        payload = {"request": case.request, "expect": case.expect}
        return "api:" + json.dumps(payload, sort_keys=True)
    words = " ".join(_WORD_RE.findall((case.title + " " + " ".join(case.steps)).lower()))
    return f"text:{case.source_ref}:{case.type}:{words}"


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    return len(a & b) / len(a | b) if a | b else 1.0


def dedupe(
    cases: list[TestCase], similarity: float = 0.9
) -> tuple[list[TestCase], list[Duplicate]]:
    """Drop exact duplicates and near-duplicates (same source and type, similar wording).

    Traces from a dropped case are merged into the kept one, so removing a duplicate never
    reduces acceptance-criteria coverage.
    """
    kept: list[TestCase] = []
    seen: dict[str, TestCase] = {}
    duplicates: list[Duplicate] = []
    for case in cases:
        match = seen.get(signature(case))
        reason = "identical"
        if match is None and case.request is None:
            words = _words(case.title + " " + " ".join(case.steps))
            for other in kept:
                if (
                    other.request is None
                    and other.source_ref == case.source_ref
                    and other.type == case.type
                    and jaccard(words, _words(other.title + " " + " ".join(other.steps)))
                    >= similarity
                ):
                    match, reason = other, "near-identical wording"
                    break
        if match is None:
            seen[signature(case)] = case
            kept.append(case)
            continue
        for trace in case.traces:
            if trace not in match.traces:
                match.traces.append(trace)
        duplicates.append(Duplicate(case.title, match.title, reason))
    return kept, duplicates
