import json

from ai_testgen.generation import generate
from ai_testgen.providers import Completion, LLMProvider, MockProvider


def test_generation_with_mock(stories, endpoints):
    result = generate(stories, endpoints, MockProvider())
    assert result.rejected == []
    assert result.schema_validity == 1.0
    assert [c.id for c in result.cases[:3]] == ["TC-001", "TC-002", "TC-003"]
    assert len({c.id for c in result.cases}) == len(result.cases)
    assert result.raw_count == len(result.cases) + len(result.duplicates)
    # A dropped duplicate's traces live on in the case that was kept.
    login = next(
        c
        for c in result.cases
        if c.title == "Protected steps of 'View order history' require login"
    )
    assert login.traces == ["US-103/AC1", "US-103/AC2"]
    summary = result.summary()
    assert summary["model_calls"] == len(stories) + len(endpoints)
    assert summary["api_cases"] == sum(c.request is not None for c in result.cases)


class ScriptedProvider(LLMProvider):
    """Returns canned replies in order, to exercise how bad model output is handled."""

    name = "scripted"

    def __init__(self, replies):
        super().__init__("scripted-1")
        self.replies = list(replies)

    def complete(self, prompt, *, system=None, max_tokens=4096, temperature=0.0):
        return Completion(self.replies.pop(0), self.model, 1, 1, 1.0)


def test_bad_model_output_is_rejected_not_patched(stories, endpoints):
    story = stories[0]
    health = endpoints[0]
    valid = {
        "title": "Basket count goes up",
        "type": "positive",
        "priority": "high",
        "steps": ["Add a book"],
        "expected": "Count is 1",
        "traces": [story.criteria[0].id],
    }
    hallucinated = {**valid, "title": "Made-up criterion", "traces": ["US-101/AC99"]}
    wrong_endpoint = {
        **valid,
        "traces": ["GET /health"],
        "request": {"method": "GET", "path": "/status"},
        "expect": {"status": 200},
    }
    provider = ScriptedProvider(
        [
            json.dumps({"test_cases": [valid, hallucinated, "not an object"]}),
            "Sorry, I cannot help with that.",
        ]
    )
    result = generate([story], [health], provider)
    assert [c.title for c in result.cases] == ["Basket count goes up"]
    assert result.raw_count == 4
    assert {r.title for r in result.rejected} == {
        "Made-up criterion",
        "(not an object)",
        "(whole response)",
    }
    assert result.schema_validity == 0.25

    provider = ScriptedProvider([json.dumps({"test_cases": [wrong_endpoint]})])
    result = generate([], [health], provider)
    assert "request targets GET /status" in result.rejected[0].errors[0]
    assert result.to_dict()["summary"]["rejected_cases"] == 1


def test_empty_generation_has_zero_validity():
    result = generate([], [], MockProvider())
    assert result.schema_validity == 0.0
