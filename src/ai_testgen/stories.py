"""Parse user stories from Markdown (with an acceptance-criteria list) or Gherkin features."""

from __future__ import annotations

import re
from pathlib import Path

from ai_testgen.models import AcceptanceCriterion, UserStory

_STORY_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")
_AC_BULLET_RE = re.compile(r"^\s*[-*]\s*(?:(AC\s*\d+)\s*[:.)-]\s*)?(.+)$", re.IGNORECASE)
_GWT_RE = re.compile(
    r"^\s*given\s+(?P<given>.+?),?\s+when\s+(?P<when>.+?),?\s+then\s+(?P<then>.+)$",
    re.IGNORECASE,
)


def split_gwt(text: str) -> tuple[str, str, str]:
    """Split an inline 'Given ..., when ..., then ...' sentence into its three parts."""
    match = _GWT_RE.match(text.strip())
    if not match:
        return "", "", ""
    return match["given"].strip(), match["when"].strip(), match["then"].strip().rstrip(".")


def _story_id(text: str, fallback: str) -> str:
    match = _STORY_ID_RE.search(text)
    return match.group(1) if match else fallback


def parse_markdown_story(text: str, source: str = "") -> UserStory:
    lines = text.splitlines()
    heading = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("#")), source)
    story_id = _story_id(heading, Path(source).stem or "STORY")
    title = re.sub(rf"^{re.escape(story_id)}\s*[:-]?\s*", "", heading).strip() or story_id

    narrative: list[str] = []
    criteria: list[AcceptanceCriterion] = []
    in_ac = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            in_ac = "acceptance" in stripped.lower()
            continue
        if not stripped:
            continue
        if in_ac:
            match = _AC_BULLET_RE.match(stripped)
            if match:
                label = (match.group(1) or f"AC{len(criteria) + 1}").replace(" ", "").upper()
                body = match.group(2).strip()
                given, when, then = split_gwt(body)
                criteria.append(AcceptanceCriterion(f"{story_id}/{label}", body, given, when, then))
        elif re.match(r"^(as an?|i want|so that)\b", stripped, re.IGNORECASE):
            narrative.append(stripped)

    if not criteria:
        raise ValueError(f"No acceptance criteria found in {source or 'story'}")
    return UserStory(story_id, title, " ".join(narrative), tuple(criteria), source)


def parse_feature(text: str, source: str = "") -> UserStory:
    """Each Gherkin Scenario becomes one acceptance criterion."""
    story_id = _story_id(text, Path(source).stem or "FEATURE")
    title = ""
    narrative: list[str] = []
    criteria: list[AcceptanceCriterion] = []
    current: dict[str, list[str]] | None = None
    current_name = ""
    last_key = "given"

    def flush() -> None:
        if current is None:
            return
        given, when, then = (" and ".join(current[k]) for k in ("given", "when", "then"))
        label = f"AC{len(criteria) + 1}"
        body = f"{current_name}: Given {given}, when {when}, then {then}"
        criteria.append(AcceptanceCriterion(f"{story_id}/{label}", body, given, when, then))

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        keyword, _, rest = line.partition(" ")
        keyword_lower = keyword.lower().rstrip(":")
        if keyword_lower == "feature":
            title = line.split(":", 1)[1].strip()
        elif keyword_lower in {"scenario", "example"}:
            flush()
            current = {"given": [], "when": [], "then": []}
            current_name = line.split(":", 1)[1].strip()
        elif current is not None and keyword_lower in {"given", "when", "then"}:
            last_key = keyword_lower
            current[last_key].append(rest.strip())
        elif current is not None and keyword_lower in {"and", "but"}:
            current[last_key].append(rest.strip())
        elif current is None and re.match(r"^(as an?|i want|so that)\b", line, re.IGNORECASE):
            narrative.append(line)
    flush()

    if not criteria:
        raise ValueError(f"No scenarios found in {source or 'feature'}")
    return UserStory(story_id, title or story_id, " ".join(narrative), tuple(criteria), source)


def load_stories(paths: list[Path]) -> list[UserStory]:
    stories = []
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8")
        parser = parse_feature if path.suffix == ".feature" else parse_markdown_story
        stories.append(parser(text, str(path.name)))
    ids = [s.id for s in stories]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"Duplicate story ids: {duplicates}")
    return stories
