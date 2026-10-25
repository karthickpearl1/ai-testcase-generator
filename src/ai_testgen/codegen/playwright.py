"""Render story-based test cases as Playwright (TypeScript) test skeletons.

The skeletons are deliberately marked ``test.fixme``: the structure, steps and traceability
are generated, but locators and assertions need a person who knows the UI. Pretending
otherwise would produce tests that pass without checking anything.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ai_testgen.models import TestCase, UserStory


def _ts(text: str) -> str:
    """A TypeScript string literal (JSON string syntax is valid TypeScript)."""
    return json.dumps(text, ensure_ascii=False)


def _sentence(prefix: str, text: str) -> str:
    """'Then' + 'The order is saved' -> 'Then the order is saved'. Keeps 'I' and acronyms."""
    first_word = text.split(" ", 1)[0]
    if first_word != "I" and len(text) > 1 and text[0].isupper() and not text[1].isupper():
        text = text[0].lower() + text[1:]
    return f"{prefix} {text}"


def _comment(text: str) -> str:
    return text.replace("*/", "* /").replace("\n", " ")


def render_test(case: TestCase) -> str:
    out = [
        f"  test.fixme({_ts(f'{case.id}: {case.title}')}, async ({{ page }}) => {{",
        f"    // Traces: {_comment(', '.join(case.traces))}",
        f"    // Type: {case.type}, priority: {case.priority}",
    ]
    for index, pre in enumerate(case.preconditions or ["The application is open"]):
        out += [
            f"    await test.step({_ts(_sentence('Given', pre))}, async () => {{",
            "      await page.goto('/'); // TODO: navigate to the right starting page"
            if index == 0
            else "      // TODO: arrange this precondition",
            "    });",
        ]
    for step in case.steps:
        out += [
            f"    await test.step({_ts(step)}, async () => {{",
            "      // TODO: perform this step, e.g.",
            "      // await page.getByRole('button', { name: '...' }).click();",
            "    });",
        ]
    out += [
        f"    await test.step({_ts(_sentence('Then', case.expected))}, async () => {{",
        "      // TODO: assert the outcome, e.g.",
        "      // await expect(page.getByTestId('...')).toHaveText('...');",
        "    });",
        "  });",
    ]
    return "\n".join(out)


def write_playwright_specs(
    cases: list[TestCase], stories: list[UserStory], out_dir: Path
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for story in stories:
        selected = [c for c in cases if c.source_kind == "story" and c.source_ref == story.id]
        if not selected:
            continue
        name = re.sub(r"[^a-z0-9]+", "-", f"{story.id} {story.title}".lower()).strip("-")
        header = [
            "import { test, expect } from '@playwright/test';",
            "",
            f"// Generated from {story.id}: {_comment(story.title)}.",
            "// Fill in locators and assertions, then change test.fixme to test.",
            "",
            f"test.describe({_ts(f'{story.id}: {story.title}')}, () => {{",
        ]
        body = "\n\n".join(render_test(c) for c in selected)
        path = out_dir / f"{name}.spec.ts"
        path.write_text("\n".join(header) + "\n" + body + "\n});\n", encoding="utf-8")
        written.append(path)
    return written
