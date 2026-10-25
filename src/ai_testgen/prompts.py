"""Generation prompts and parsing of the model's JSON reply."""

from __future__ import annotations

import json
import re
from typing import Any

from ai_testgen.providers.base import ProviderError

SYSTEM_PROMPT = (
    "You are a senior test engineer. Design concise, independent test cases using equivalence "
    "partitioning, boundary value analysis, negative testing and basic security testing. "
    "Reply with a single JSON object and nothing else."
)

_CASE_FORMAT = """Return JSON of the form {"test_cases": [ ... ]} where each test case has:
  "title": short imperative description,
  "type": one of "positive", "negative", "boundary", "security",
  "priority": one of "high", "medium", "low",
  "preconditions": list of strings,
  "steps": non-empty list of strings,
  "expected": the observable expected result,
  "traces": non-empty list of the ids this case verifies,
  "tags": list of strings"""

STORY_PROMPT = """Design test cases for the user story below.
Every acceptance criterion must be covered by at least one test case. Use the acceptance
criterion ids (for example "US-101/AC2") in "traces".

{case_format}

<story>
{payload}
</story>"""

ENDPOINT_PROMPT = """Design API test cases for the OpenAPI operation below.
Cover the success path, validation failures, boundaries of every constrained field, missing
or invalid authentication when the operation is secured, and one injection-style payload.
Only use status codes documented in "responses". In "traces" put the operation id and
"<operation id> <status>" for the status each case expects.

{case_format}
Each API test case must also have:
  "request": {{"method", "path" (the templated path), "path_params", "query", "body",
              "auth": "valid" | "none" | "invalid"}},
  "expect": {{"status": int}} or {{"status_in": [int, ...]}}, optionally "body_keys" (list of
            top-level keys that must be present) or "body_type": "array".

<endpoint>
{payload}
</endpoint>"""


def story_prompt(story: dict[str, Any]) -> str:
    return STORY_PROMPT.format(case_format=_CASE_FORMAT, payload=json.dumps(story, indent=2))


def endpoint_prompt(endpoint: dict[str, Any]) -> str:
    return ENDPOINT_PROMPT.format(case_format=_CASE_FORMAT, payload=json.dumps(endpoint, indent=2))


def parse_cases(text: str) -> list[Any]:
    """Extract the ``test_cases`` list, tolerating code fences or prose around the JSON."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ProviderError(f"Model reply contained no JSON object: {text[:200]!r}")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Model reply was not valid JSON: {exc}") from exc
    cases = data.get("test_cases") if isinstance(data, dict) else None
    if not isinstance(cases, list):
        raise ProviderError("Model reply has no 'test_cases' list")
    return cases
