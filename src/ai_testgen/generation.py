"""The generation pipeline: prompt the model, validate its output, dedupe, assign ids."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ai_testgen.dedupe import Duplicate, dedupe
from ai_testgen.models import Endpoint, TestCase, UserStory
from ai_testgen.prompts import SYSTEM_PROMPT, endpoint_prompt, parse_cases, story_prompt
from ai_testgen.providers import LLMProvider, ProviderError
from ai_testgen.schema import validate_api_case, validate_story_case


@dataclass
class Rejected:
    source: str
    title: str
    errors: list[str]


@dataclass
class GenerationResult:
    stories: list[UserStory]
    endpoints: list[Endpoint]
    cases: list[TestCase]
    raw_count: int
    rejected: list[Rejected] = field(default_factory=list)
    duplicates: list[Duplicate] = field(default_factory=list)
    usage: dict[str, float] = field(default_factory=dict)

    @property
    def schema_validity(self) -> float:
        return (
            round((self.raw_count - len(self.rejected)) / self.raw_count, 4)
            if self.raw_count
            else 0.0
        )

    def summary(self) -> dict[str, Any]:
        return {
            "stories": len(self.stories),
            "acceptance_criteria": sum(len(s.criteria) for s in self.stories),
            "endpoints": len(self.endpoints),
            "raw_cases": self.raw_count,
            "rejected_cases": len(self.rejected),
            "schema_validity": self.schema_validity,
            "duplicates_removed": len(self.duplicates),
            "final_cases": len(self.cases),
            "api_cases": sum(c.request is not None for c in self.cases),
            **self.usage,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "cases": [c.to_dict() for c in self.cases],
            "rejected": [asdict(r) for r in self.rejected],
            "duplicates": [asdict(d) for d in self.duplicates],
        }


def _title(raw: Any) -> str:
    return str(raw.get("title", "(untitled)")) if isinstance(raw, dict) else "(not an object)"


def _to_case(raw: dict[str, Any], kind: str, ref: str) -> TestCase:
    return TestCase(
        title=raw["title"],
        type=raw["type"],
        priority=raw["priority"],
        steps=list(raw["steps"]),
        expected=raw["expected"],
        traces=list(raw["traces"]),
        source_kind=kind,
        source_ref=ref,
        preconditions=list(raw.get("preconditions", [])),
        tags=list(raw.get("tags", [])),
        request=raw.get("request"),
        expect=raw.get("expect"),
    )


def generate(
    stories: list[UserStory], endpoints: list[Endpoint], provider: LLMProvider
) -> GenerationResult:
    collected: list[TestCase] = []
    rejected: list[Rejected] = []
    raw_count = 0
    usage = {"model_calls": 0, "input_tokens": 0, "output_tokens": 0, "model_latency_ms": 0.0}

    def ask(prompt: str, source: str) -> list[Any]:
        nonlocal raw_count
        completion = provider.complete(prompt, system=SYSTEM_PROMPT)
        usage["model_calls"] += 1
        usage["input_tokens"] += completion.input_tokens
        usage["output_tokens"] += completion.output_tokens
        usage["model_latency_ms"] = round(usage["model_latency_ms"] + completion.latency_ms, 1)
        try:
            items = parse_cases(completion.text)
        except ProviderError as exc:
            raw_count += 1
            rejected.append(Rejected(source, "(whole response)", [str(exc)]))
            return []
        raw_count += len(items)
        return items

    for story in stories:
        criteria_ids = {ac.id for ac in story.criteria}
        payload = {
            "id": story.id,
            "title": story.title,
            "narrative": story.narrative,
            "criteria": [asdict(ac) for ac in story.criteria],
        }
        for raw in ask(story_prompt(payload), story.id):
            errors = validate_story_case(raw, criteria_ids)
            if errors:
                rejected.append(Rejected(story.id, _title(raw), errors))
            else:
                collected.append(_to_case(raw, "story", story.id))

    for endpoint in endpoints:
        payload = endpoint.to_prompt_dict()
        for raw in ask(endpoint_prompt(payload), endpoint.id):
            errors = validate_api_case(raw, payload)
            if errors:
                rejected.append(Rejected(endpoint.id, _title(raw), errors))
            else:
                collected.append(_to_case(raw, "openapi", endpoint.id))

    cases, duplicates = dedupe(collected)
    for number, case in enumerate(cases, start=1):
        case.id = f"TC-{number:03d}"
    return GenerationResult(stories, endpoints, cases, raw_count, rejected, duplicates, usage)
