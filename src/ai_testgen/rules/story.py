"""Test design rules for a user story's acceptance criteria."""

from __future__ import annotations

import re
from typing import Any

_RANGE_PATTERNS = (
    (re.compile(r"between (\d+) and (\d+)(?: (\w+))?", re.I), "both"),
    (
        re.compile(r"at least (\d+)(?: (\w+))?.*?(?:no more than|at most|up to) (\d+)", re.I),
        "both2",
    ),
    (re.compile(r"(?:no more than|at most|up to|maximum of) (\d+)(?: (\w+))?", re.I), "max"),
    (re.compile(r"(?:at least|minimum of) (\d+)(?: (\w+))?", re.I), "min"),
)
_NEGATIVE_RE = re.compile(
    r"\b(cannot|can't|must not|rejected|not allowed|invalid|denied|required|already|never)\b",
    re.I,
)
_AUTH_RE = re.compile(r"\b(logged in|log in|login|sign in)\b", re.I)
_VALIDATION_RE = re.compile(r"\b(must|should) be\b|\brequired\b", re.I)
_OTHER_USER_RE = re.compile(r"\b(another|different) (customer|user)\b", re.I)
_SECRET_RE = re.compile(r"\bpassword\b.*\b(plain text|shown|never)\b", re.I)
_INPUT_FIELDS = ("email address", "display name", "password", "search", "comment", "title")
_QUOTED_RE = re.compile(r"\"([^\"]+)\"")
_SUBJECT_RE = re.compile(r"^(?:the |a |an )?(.+?)\s+(?:must|should|is|are|cannot|can)\b", re.I)
_UNITS = {"characters", "character", "items", "books", "orders", "digits"}


def _short(text: str, limit: int = 80) -> str:
    text = text.strip().rstrip(".")
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _subject(text: str) -> str:
    match = _SUBJECT_RE.match(text.strip())
    if not match:
        return "value"
    words = []
    for word in match.group(1).split():
        if word.lower() in {"of", "in", "on", "for", "that", "with"}:
            break
        words.append(word)
    return " ".join(words) or "value"


def _range(text: str) -> tuple[int | None, int | None, str]:
    """Extract (minimum, maximum, unit) from phrases like 'between 1 and 10'."""
    for pattern, kind in _RANGE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        if kind == "both":
            low, high, unit = int(match[1]), int(match[2]), match[3] or ""
        elif kind == "both2":
            low, high, unit = int(match[1]), int(match[3]), match[2] or ""
        elif kind == "max":
            low, high, unit = None, int(match[1]), match[2] or ""
        else:
            low, high, unit = int(match[1]), None, match[2] or ""
        return low, high, unit if unit.lower() in _UNITS else ""
    return None, None, ""


def _case(
    title: str,
    case_type: str,
    priority: str,
    steps: list[str],
    expected: str,
    trace: str,
    story_id: str,
    preconditions: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "title": title,
        "type": case_type,
        "priority": priority,
        "preconditions": preconditions or [],
        "steps": steps,
        "expected": expected,
        "traces": [trace],
        "tags": [story_id, case_type],
    }


def _rule_text(ac: dict[str, Any]) -> str:
    """The criterion without a Gherkin scenario's Given/When/Then tail."""
    return ac["text"].split(": Given")[0]


def _positive(story: dict[str, Any], ac: dict[str, Any]) -> list[dict[str, Any]]:
    if ac.get("when"):
        return [
            _case(
                f"Verify {_short(ac['then'], 70)}",
                "positive",
                "high",
                [ac["when"][0].upper() + ac["when"][1:]],
                ac["then"][0].upper() + ac["then"][1:],
                ac["id"],
                story["id"],
                [ac["given"][0].upper() + ac["given"][1:]] if ac.get("given") else [],
            )
        ]
    text = ac["text"]
    low, high, _ = _range(text)
    if low is not None or high is not None:
        subject = _subject(text)
        return [
            _case(
                f"A valid {subject} within the allowed range is accepted",
                "positive",
                "high",
                [
                    f"Go to the '{story['title']}' journey",
                    f"Enter a typical valid {subject}",
                    "Submit",
                ],
                "The value is accepted and the journey continues",
                ac["id"],
                story["id"],
            )
        ]
    if _NEGATIVE_RE.search(text):
        return []  # purely prohibitive rules are covered by negative/security cases
    return [
        _case(
            f"Verify {_short(text, 70)}",
            "positive",
            "high",
            [f"Go to the '{story['title']}' journey", "Perform the action described"],
            _short(text, 160),
            ac["id"],
            story["id"],
        )
    ]


def _boundaries(story: dict[str, Any], ac: dict[str, Any]) -> list[dict[str, Any]]:
    low, high, unit = _range(ac["text"])
    if low is None and high is None:
        return []
    subject = _subject(ac["text"])
    probes: list[tuple[int, str, bool]] = []
    if low is not None:
        if low > 0:
            probes.append((low - 1, f"below minimum {low}", False))
        probes.append((low, "minimum", True))
    if high is not None:
        probes.append((high, "maximum", True))
        probes.append((high + 1, f"above maximum {high}", False))

    is_validation = bool(_VALIDATION_RE.search(ac["text"]))
    cases = []
    for value, label, valid in probes:
        amount = f"{value} {unit}" if unit else str(value)
        if is_validation:
            what = f"with {amount}" if unit else f"of {amount}"
            title = f"{subject.capitalize()} {what} is {'accepted' if valid else 'rejected'}"
            steps = [f"Go to the '{story['title']}' journey", f"Enter a {subject} {what}", "Submit"]
            expected = (
                "The value is accepted" if valid else "A validation message explains the limit"
            )
        else:
            # A behavioural limit (e.g. page size) rather than an input rule.
            title = f"Behaviour at {amount}"
            steps = [f"Set up data so the scenario involves {amount}"]
            if ac.get("when"):
                steps.append(ac["when"][0].upper() + ac["when"][1:])
            expected = (
                "The rule holds exactly at the limit"
                if valid
                else f"The limit is enforced: {_short(ac.get('then') or ac['text'], 100)}"
            )
        cases.append(
            _case(
                f"{title} ({label})",
                "boundary",
                "medium",
                steps,
                expected,
                ac["id"],
                story["id"],
            )
        )
    return cases


def _negatives(story: dict[str, Any], ac: dict[str, Any]) -> list[dict[str, Any]]:
    text = ac["text"]
    if not _NEGATIVE_RE.search(text) or _SECRET_RE.search(text):
        return []
    quoted = _QUOTED_RE.findall(ac.get("then") or text)
    expected = (
        f'The message "{quoted[-1]}" is shown'
        if quoted
        else "The action is blocked with a clear message"
    )
    if re.search(r"\brequired\b", text, re.I):
        subject = _subject(text)
        return [
            _case(
                f"Submitting without {subject} is rejected",
                "negative",
                "medium",
                [f"Go to the '{story['title']}' journey", f"Leave {subject} empty", "Submit"],
                f"A validation message says {subject} is required",
                ac["id"],
                story["id"],
            )
        ]
    return [
        _case(
            f"Rule is enforced: {_short(_rule_text(ac), 70)}",
            "negative",
            "medium",
            [f"Go to the '{story['title']}' journey", "Attempt the action the rule forbids"],
            expected,
            ac["id"],
            story["id"],
        )
    ]


def _security(story: dict[str, Any], ac: dict[str, Any]) -> list[dict[str, Any]]:
    text = ac["text"]
    cases = []
    if _OTHER_USER_RE.search(text):
        cases.append(
            _case(
                "Changing the record id in the URL does not expose another customer's data",
                "security",
                "high",
                ["Log in as customer A", "Open a URL containing customer B's record id"],
                "Access is denied and no data belonging to customer B is shown",
                ac["id"],
                story["id"],
            )
        )
    elif _AUTH_RE.search(ac.get("given", "")) or re.search(
        r"\b(asked to|must) log in\b", text, re.I
    ):
        cases.append(
            _case(
                f"Protected steps of '{story['title']}' require login",
                "security",
                "high",
                ["Make sure no user is logged in", f"Go directly to the '{story['title']}' pages"],
                "The user is asked to log in and no protected data is shown",
                ac["id"],
                story["id"],
            )
        )
    if _SECRET_RE.search(text):
        cases.append(
            _case(
                "Password is masked on screen and never echoed back",
                "security",
                "high",
                ["Type a password into the form", "Submit", "Check the page and any emails sent"],
                "The password is masked while typing and never appears in plain text",
                ac["id"],
                story["id"],
            )
        )
    for field in _INPUT_FIELDS:
        if field in text.lower():
            cases.append(
                _case(
                    f"Injection payloads in the {field} field are rejected or safely escaped",
                    "security",
                    "medium",
                    [
                        f"Enter <script>alert(1)</script> and ' OR '1'='1 in the {field} field",
                        "Submit",
                    ],
                    "Input is rejected or rendered as plain text; no script runs, no server error",
                    ac["id"],
                    story["id"],
                )
            )
    return cases


def cases_for_story(story: dict[str, Any]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for ac in story["criteria"]:
        cases.extend(_positive(story, ac))
        cases.extend(_boundaries(story, ac))
        cases.extend(_negatives(story, ac))
        cases.extend(_security(story, ac))
    return cases
