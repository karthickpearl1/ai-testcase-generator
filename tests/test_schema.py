import copy

import pytest

from ai_testgen.rules import cases_for_endpoint
from ai_testgen.schema import schema_errors, validate_api_case, validate_story_case

STORY_CASE = {
    "title": "Valid quantity is accepted",
    "type": "positive",
    "priority": "high",
    "steps": ["Enter 2"],
    "expected": "Accepted",
    "traces": ["US-1/AC1"],
}


def test_valid_story_case():
    assert validate_story_case(STORY_CASE, {"US-1/AC1"}) == []


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        ({"type": "smoke"}, "type"),
        ({"steps": []}, "steps"),
        ({"surprise": 1}, "Additional properties"),
        ({"priority": "urgent"}, "priority"),
    ],
)
def test_schema_violations(change, fragment):
    errors = schema_errors({**STORY_CASE, **change})
    assert errors
    assert fragment in " ".join(errors)


def test_missing_field_and_non_object():
    case = dict(STORY_CASE)
    del case["expected"]
    assert "'expected' is a required property" in schema_errors(case)[0]
    assert schema_errors(["not", "a", "dict"]) == ["test case is not a JSON object"]


def test_unknown_trace_is_rejected():
    errors = validate_story_case(STORY_CASE, {"US-2/AC1"})
    assert "unknown acceptance criteria" in errors[0]


@pytest.fixture
def api_case(endpoint_dicts):
    return cases_for_endpoint(endpoint_dicts["GET /books/{bookId}"])[0]


def test_valid_api_case(api_case, endpoint_dicts):
    assert validate_api_case(api_case, endpoint_dicts["GET /books/{bookId}"]) == []


def test_api_case_semantic_checks(api_case, endpoint_dicts):
    endpoint = endpoint_dicts["GET /books/{bookId}"]

    wrong_path = copy.deepcopy(api_case)
    wrong_path["request"]["path"] = "/books"
    assert "request targets" in validate_api_case(wrong_path, endpoint)[0]

    no_params = copy.deepcopy(api_case)
    no_params["request"]["path_params"] = {}
    assert "missing path parameters" in validate_api_case(no_params, endpoint)[0]

    undocumented = copy.deepcopy(api_case)
    undocumented["expect"] = {"status": 418}
    assert "undocumented" in validate_api_case(undocumented, endpoint)[0]

    story_shaped = {k: v for k, v in api_case.items() if k not in ("request", "expect")}
    assert "need 'request'" in validate_api_case(story_shaped, endpoint)[0]

    assert validate_api_case({"title": "x"}, endpoint)
