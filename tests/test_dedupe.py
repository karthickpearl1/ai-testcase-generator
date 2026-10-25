from ai_testgen.dedupe import dedupe, jaccard
from ai_testgen.models import TestCase


def make(title, traces, steps=("Do it",), ref="US-1", request=None, expect=None, kind="story"):
    return TestCase(
        title=title,
        type="positive",
        priority="high",
        steps=list(steps),
        expected="Done",
        traces=list(traces),
        source_kind=kind,
        source_ref=ref,
        request=request,
        expect=expect,
    )


def test_identical_story_cases_merge_traces():
    kept, duplicates = dedupe(
        [make("Login required", ["US-1/AC1"]), make("Login required", ["US-1/AC2"])]
    )
    assert len(kept) == 1
    assert kept[0].traces == ["US-1/AC1", "US-1/AC2"]
    assert duplicates[0].reason == "identical"


def test_near_duplicates_by_wording():
    a = make("Password is masked on the screen", ["US-1/AC1"], steps=["Type a password", "Submit"])
    b = make("password is masked on the screen.", ["US-1/AC1"], steps=["Type a password", "Submit"])
    c = make("Password is masked", ["US-1/AC1"], steps=["Open the form"])
    kept, duplicates = dedupe([a, b, c])
    assert [k.title for k in kept] == [a.title, c.title]
    assert len(duplicates) == 1


def test_same_wording_in_different_stories_is_kept():
    kept, _ = dedupe(
        [make("Login required", ["US-1/AC1"]), make("Login required", ["US-2/AC1"], ref="US-2")]
    )
    assert len(kept) == 2


def test_api_cases_compare_request_and_expectation():
    request = {"method": "GET", "path": "/x", "auth": "none"}
    a = make("Get x", ["GET /x"], request=request, expect={"status": 200}, kind="openapi")
    b = make(
        "Different title, same call",
        ["GET /x 200"],
        request=dict(request),
        expect={"status": 200},
        kind="openapi",
    )
    c = make(
        "Get x expecting 404",
        ["GET /x"],
        request=dict(request),
        expect={"status": 404},
        kind="openapi",
    )
    kept, duplicates = dedupe([a, b, c])
    assert [k.title for k in kept] == ["Get x", "Get x expecting 404"]
    assert kept[0].traces == ["GET /x", "GET /x 200"]
    assert len(duplicates) == 1


def test_jaccard():
    assert jaccard(frozenset(), frozenset()) == 1.0
    assert jaccard(frozenset("ab"), frozenset("bc")) == 1 / 3
