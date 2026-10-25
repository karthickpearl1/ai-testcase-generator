"""Offline, deterministic stand-in for an LLM.

The mock reads the ``<story>`` or ``<endpoint>`` JSON block from the generation prompt and
answers with test cases designed by the rules in :mod:`ai_testgen.rules`, serialised as the
same JSON a real model is asked to return. Everything downstream (schema validation, dedupe,
code generation, execution, mutation testing) therefore runs exactly as it would with a
real model, but reproducibly and without keys.

Three knobs simulate the ways real models go wrong, so the quality gate can be demonstrated:
``invalid_rate`` emits malformed cases, ``duplicate_rate`` emits near-duplicates, and
``weak_assertions`` makes API cases accept any documented status code, the kind of test that
always passes and catches nothing.
"""

from __future__ import annotations

import hashlib
import json
import re

from ai_testgen.providers.base import Completion, LLMProvider, estimate_tokens
from ai_testgen.rules import cases_for_endpoint, cases_for_story

_BLOCK_RE = re.compile(r"<(story|endpoint)>\s*(.*?)\s*</\1>", re.DOTALL)


def _unit_hash(*parts: str) -> float:
    digest = hashlib.sha256("\x1f".join(parts).encode()).hexdigest()
    return int(digest[:12], 16) / float(16**12)


class MockProvider(LLMProvider):
    name = "mock"

    def __init__(
        self,
        model: str = "mock-rules-v1",
        *,
        invalid_rate: float = 0.0,
        duplicate_rate: float = 0.0,
        weak_assertions: bool = False,
        seed: str = "0",
    ) -> None:
        super().__init__(model)
        for label, rate in (("invalid_rate", invalid_rate), ("duplicate_rate", duplicate_rate)):
            if not 0.0 <= rate <= 1.0:
                raise ValueError(f"{label} must be between 0 and 1")
        self.invalid_rate = invalid_rate
        self.duplicate_rate = duplicate_rate
        self.weak_assertions = weak_assertions
        self.seed = seed

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        match = _BLOCK_RE.search(prompt)
        if match is None:
            text = json.dumps({"test_cases": []})
        else:
            kind, payload = match.group(1), json.loads(match.group(2))
            if kind == "story":
                cases = cases_for_story(payload)
            else:
                cases = cases_for_endpoint(payload)
                if self.weak_assertions:
                    documented = sorted(int(code) for code in payload["responses"])
                    for case in cases:
                        case["expect"] = {"status_in": documented}
            text = json.dumps({"test_cases": self._degrade(cases)}, indent=1)

        input_tokens = estimate_tokens((system or "") + prompt)
        output_tokens = estimate_tokens(text)
        latency_ms = 300.0 + 0.05 * input_tokens + 8.0 * output_tokens
        return Completion(text, self.model, input_tokens, output_tokens, round(latency_ms, 1))

    def _degrade(self, cases: list[dict]) -> list[dict]:
        out: list[dict] = []
        for case in cases:
            key = case["title"]
            if _unit_hash(self.seed, "invalid", key) < self.invalid_rate:
                broken = dict(case)
                # Alternate between the two most common malformations seen from real models.
                if _unit_hash("which", key) < 0.5:
                    broken.pop("expected")
                else:
                    broken["type"] = "smoke"
                out.append(broken)
            else:
                out.append(case)
            if _unit_hash(self.seed, "duplicate", key) < self.duplicate_rate:
                copy = dict(case)
                copy["title"] = case["title"].lower() + "."
                out.append(copy)
        return out
