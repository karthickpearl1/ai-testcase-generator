"""Core data model shared by the parsers, generators, exporters and evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

CASE_TYPES = ("positive", "negative", "boundary", "security")
PRIORITIES = ("high", "medium", "low")


@dataclass(frozen=True)
class AcceptanceCriterion:
    id: str  # e.g. "US-101/AC2"
    text: str
    given: str = ""
    when: str = ""
    then: str = ""


@dataclass(frozen=True)
class UserStory:
    id: str
    title: str
    narrative: str
    criteria: tuple[AcceptanceCriterion, ...]
    source: str = ""


@dataclass(frozen=True)
class Parameter:
    name: str
    location: str  # path | query | header
    required: bool
    schema: dict[str, Any]


@dataclass(frozen=True)
class Endpoint:
    method: str
    path: str
    operation_id: str
    summary: str
    parameters: tuple[Parameter, ...]
    request_schema: dict[str, Any] | None
    responses: dict[int, dict[str, Any] | None]  # status -> resolved body schema (or None)
    requires_auth: bool

    @property
    def id(self) -> str:
        return f"{self.method} {self.path}"

    def response_ids(self) -> list[str]:
        return [f"{self.id} {status}" for status in sorted(self.responses)]

    def to_prompt_dict(self) -> dict[str, Any]:
        """A compact, JSON-serialisable view of the operation for the generation prompt."""
        return {
            "id": self.id,
            "method": self.method,
            "path": self.path,
            "summary": self.summary,
            "requires_auth": self.requires_auth,
            "parameters": [asdict(p) for p in self.parameters],
            "request_schema": self.request_schema,
            "responses": {str(k): v for k, v in sorted(self.responses.items())},
        }


@dataclass
class TestCase:
    """A generated test case.

    ``request``/``expect`` are only present for API cases and are what the pytest code
    generator turns into executable tests. ``traces`` links the case back to acceptance
    criteria ids or ``"METHOD /path STATUS"`` response ids for coverage mapping.
    """

    __test__ = False  # stop pytest trying to collect this class

    title: str
    type: str
    priority: str
    steps: list[str]
    expected: str
    traces: list[str]
    source_kind: str  # story | openapi
    source_ref: str  # story id or endpoint id
    preconditions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    request: dict[str, Any] | None = None
    expect: dict[str, Any] | None = None
    id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestCase:
        return cls(**data)
