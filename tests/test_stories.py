import pytest

from ai_testgen.stories import load_stories, parse_feature, parse_markdown_story, split_gwt


def test_markdown_story(stories):
    story = next(s for s in stories if s.id == "US-101")
    assert story.title == "Add a book to the basket"
    assert story.narrative.startswith("As a customer")
    assert [ac.id for ac in story.criteria] == [f"US-101/AC{i}" for i in range(1, 5)]
    assert story.criteria[0].when == 'I click "Add to basket"'


def test_feature_scenarios_become_criteria(stories):
    story = next(s for s in stories if s.id == "US-103")
    assert story.title == "View order history"
    assert len(story.criteria) == 3
    first = story.criteria[0]
    assert first.given == "I am logged in and have placed 3 orders"
    assert first.then == "I see 3 orders listed with the newest first"


def test_split_gwt():
    assert split_gwt("Given a, when b, then c.") == ("a", "b", "c")
    assert split_gwt("The password must be long") == ("", "", "")


def test_unlabelled_bullets_are_numbered():
    story = parse_markdown_story("# ABC-7: Thing\n\n## Acceptance criteria\n- first\n- second\n")
    assert [ac.id for ac in story.criteria] == ["ABC-7/AC1", "ABC-7/AC2"]


def test_feature_and_but_steps_attach_to_previous_keyword():
    story = parse_feature(
        "Feature: F\n  Scenario: S\n    Given a\n    And b\n    When c\n    Then d\n    But e\n",
        "X-1.feature",
    )
    ac = story.criteria[0]
    assert ac.given == "a and b"
    assert ac.then == "d and e"
    assert story.id == "X-1"


@pytest.mark.parametrize(
    ("parser", "text"),
    [(parse_markdown_story, "# US-1: no criteria\n"), (parse_feature, "Feature: nothing\n")],
)
def test_missing_criteria_is_an_error(parser, text):
    with pytest.raises(ValueError, match="No"):
        parser(text)


def test_duplicate_story_ids(tmp_path):
    for name in ("a.md", "b.md"):
        (tmp_path / name).write_text("# US-9: x\n\n## Acceptance criteria\n- one\n")
    with pytest.raises(ValueError, match="Duplicate"):
        load_stories(list(tmp_path.iterdir()))
