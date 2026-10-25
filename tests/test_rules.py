from dataclasses import asdict

import pytest

from ai_testgen.rules import cases_for_endpoint, cases_for_story
from ai_testgen.rules.api import INJECTION_PAYLOAD, NOT_FOUND_ID, build_body, example_for
from ai_testgen.rules.story import _range, _subject


@pytest.mark.parametrize(
    ("schema", "value"),
    [
        ({"type": "string", "example": "a"}, "a"),
        ({"type": "string", "enum": ["x", "y"]}, "x"),
        ({"type": "string", "minLength": 3}, "xxx"),
        ({"type": "integer", "minimum": 5}, 5),
        ({"type": "number"}, 1.0),
        ({"type": "boolean"}, True),
        ({"type": "array"}, []),
        ({"type": "object", "required": ["a"], "properties": {"a": {"type": "integer"}}}, {"a": 1}),
        ({}, None),
    ],
)
def test_example_for(schema, value):
    assert example_for(schema) == value


def test_build_body_includes_required_and_exemplified_optional_fields():
    schema = {
        "required": ["a"],
        "properties": {"a": {"type": "string"}, "b": {"example": 2}, "c": {"type": "string"}},
    }
    assert build_body(schema) == {"a": "x", "b": 2}


def _by_title(cases):
    return {c["title"]: c for c in cases}


def test_create_book_cases(endpoint_dicts):
    cases = _by_title(cases_for_endpoint(endpoint_dicts["POST /books"]))
    positive = cases["Add a book to the catalogue succeeds with valid input"]
    assert positive["expect"]["status"] == 201
    assert "author" in positive["expect"]["body_keys"]
    assert positive["request"]["auth"] == "valid"

    above = cases["Add a book to the catalogue: 'title' above maximum length (120) is rejected"]
    assert above["request"]["body"]["title"] == "x" * 121
    assert above["expect"] == {"status": 400}
    assert above["traces"] == ["POST /books", "POST /books 400"]

    price = cases["Add a book to the catalogue: 'price' below minimum (0.01) is rejected"]
    assert price["request"]["body"]["price"] == 0.0

    injection = next(c for c in cases.values() if "injection" in c["title"])
    assert injection["request"]["body"]["title"] == INJECTION_PAYLOAD
    assert injection["expect"] == {"status_in": [201, 400]}
    auth = {c["request"]["auth"] for c in cases.values() if c["type"] == "security"}
    assert auth == {"none", "invalid", "valid"}


def test_not_found_cases(endpoint_dicts):
    get_cases = cases_for_endpoint(endpoint_dicts["GET /books/{bookId}"])
    not_found = next(c for c in get_cases if c["expect"].get("status") == 404)
    assert not_found["request"]["path_params"] == {"bookId": NOT_FOUND_ID}
    order_cases = cases_for_endpoint(endpoint_dicts["POST /orders"])
    assert any(c["request"]["body"].get("book_id") == NOT_FOUND_ID for c in order_cases)


def test_query_boundaries(endpoint_dicts):
    cases = cases_for_endpoint(endpoint_dicts["GET /books"])
    limits = sorted(c["request"]["query"]["limit"] for c in cases if c["request"]["query"])
    assert limits == [0, 1, 100, 101]


def test_no_invalid_cases_without_a_documented_validation_status():
    endpoint = {
        "id": "POST /x",
        "method": "POST",
        "path": "/x",
        "summary": "",
        "requires_auth": False,
        "parameters": [],
        "request_schema": {
            "required": ["n"],
            "properties": {"n": {"type": "integer", "minimum": 1, "maximum": 3}},
        },
        "responses": {"200": None},
    }
    cases = cases_for_endpoint(endpoint)
    assert {c["expect"]["status"] for c in cases} == {200}
    assert cases[0]["title"].startswith("POST /x")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("must be between 1 and 10", (1, 10, "")),
        ("at least 8 characters and no more than 64 characters", (8, 64, "characters")),
        ("no more than 30 characters", (None, 30, "characters")),
        ("a minimum of 3 items", (3, None, "items")),
        ("at most 20 orders per page", (None, 20, "orders")),
        ("nothing numeric", (None, None, "")),
    ],
)
def test_range_extraction(text, expected):
    assert _range(text) == expected


def test_subject_extraction():
    assert _subject("The quantity of a single book must be between 1 and 10") == "quantity"
    assert _subject("The display name is required") == "display name"
    assert _subject("Something happens") == "value"


def _story_cases(stories, story_id):
    story = next(s for s in stories if s.id == story_id)
    return cases_for_story(asdict(story))


def test_story_cases_cover_every_criterion(stories):
    for story in stories:
        traces = {t for c in _story_cases(stories, story.id) for t in c["traces"]}
        assert traces == {ac.id for ac in story.criteria}


def test_validation_boundaries_and_behavioural_limits(stories):
    titles = [c["title"] for c in _story_cases(stories, "US-102")]
    assert "Password with 7 characters is rejected (below minimum 8)" in titles
    assert "Password with 65 characters is rejected (above maximum 64)" in titles
    orders = [c["title"] for c in _story_cases(stories, "US-103")]
    assert "Behaviour at 21 orders (above maximum 20)" in orders


def test_negative_and_security_cases(stories):
    cases = _story_cases(stories, "US-102")
    titles = {c["title"]: c for c in cases}
    assert "Submitting without display name is rejected" in titles
    duplicate_email = next(
        c for t, c in titles.items() if t.startswith("Rule is enforced: An email")
    )
    assert (
        duplicate_email["expected"]
        == 'The message "An account with this email already exists" is shown'
    )
    assert "Password is masked on screen and never echoed back" in titles
    idor = [c for c in _story_cases(stories, "US-103") if "another customer" in c["title"]]
    assert idor
    assert idor[0]["type"] == "security"
