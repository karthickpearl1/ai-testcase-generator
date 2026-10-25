"""Evaluate generated API tests by running them, then mutation-testing them.

Passing tests prove little on their own: a test that asserts nothing always passes. So the
suite is also run against copies of the demo API with one injected bug each. A mutant is
"killed" when a test that passed against the correct API fails against the mutant. The share
of mutants killed (the mutation score) measures whether the tests would catch real defects.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ai_testgen.demo_api import DEMO_TOKEN, MUTANTS, running_server

_TC_RE = re.compile(r"test_tc_(\d+)")


@dataclass
class SuiteRun:
    outcomes: dict[str, str]  # TC id -> passed | failed | error | skipped
    failures: dict[str, str] = field(default_factory=dict)  # TC id -> first line of message

    @property
    def passed(self) -> set[str]:
        return {tc for tc, outcome in self.outcomes.items() if outcome == "passed"}


@dataclass
class MutantResult:
    name: str
    description: str
    killed: bool
    killed_by: list[str]


def _tc_id(test_name: str) -> str:
    match = _TC_RE.search(test_name)
    return f"TC-{match.group(1)}" if match else test_name


def run_suite(
    suite_dir: Path, base_url: str, token: str = DEMO_TOKEN, timeout: int = 300
) -> SuiteRun:
    """Run the generated pytest suite in a subprocess and parse its JUnit XML."""
    with tempfile.TemporaryDirectory() as tmp:
        junit = Path(tmp) / "junit.xml"
        env = {**os.environ, "API_BASE_URL": base_url, "API_TOKEN": token}
        env.pop("PYTEST_ADDOPTS", None)
        command = [
            sys.executable,
            "-m",
            "pytest",
            str(suite_dir),
            "-c",
            str(suite_dir / "pytest.ini"),
            "--rootdir",
            str(suite_dir),
            "-p",
            "no:cacheprovider",
            "-q",
            f"--junitxml={junit}",
        ]
        subprocess.run(
            command, env=env, capture_output=True, text=True, timeout=timeout, check=False
        )
        if not junit.exists():
            raise RuntimeError(f"pytest produced no results for {suite_dir}")
        root = ET.parse(junit).getroot()

    run = SuiteRun({})
    for case in root.iter("testcase"):
        tc = _tc_id(case.get("name", ""))
        outcome = "passed"
        for tag in ("failure", "error", "skipped"):
            node = case.find(tag)
            if node is not None:
                outcome = "failed" if tag == "failure" else tag
                message = (node.get("message") or "").strip().splitlines()
                run.failures[tc] = message[0][:200] if message else tag
                break
        run.outcomes[tc] = outcome
    return run


def mutation_test(
    suite_dir: Path, baseline: SuiteRun, mutants: dict[str, str] | None = None
) -> list[MutantResult]:
    results = []
    for name, description in (mutants or MUTANTS).items():
        with running_server(mutant=name) as url:
            run = run_suite(suite_dir, url)
        killers = sorted(tc for tc in baseline.passed if run.outcomes.get(tc) != "passed")
        results.append(MutantResult(name, description, bool(killers), killers))
    return results


def evaluate_suite(
    suite_dir: Path,
    *,
    base_url: str | None = None,
    mutation: bool = True,
) -> dict[str, Any]:
    """Execute the suite (against ``base_url`` or a fresh demo API) and optionally mutate."""
    if base_url:
        clean = run_suite(suite_dir, base_url, os.environ.get("API_TOKEN", DEMO_TOKEN))
        mutation = False  # mutants only exist for the bundled demo API
    else:
        with running_server() as url:
            clean = run_suite(suite_dir, url)

    total = len(clean.outcomes)
    metrics: dict[str, Any] = {
        "api_tests_executed": total,
        "api_tests_passed": len(clean.passed),
        "execution_pass_rate": round(len(clean.passed) / total, 4) if total else 0.0,
    }
    details: dict[str, Any] = {
        "failing_tests": {
            tc: clean.failures.get(tc, "") for tc in sorted(set(clean.outcomes) - clean.passed)
        },
        "mutants": [],
    }
    if mutation:
        results = mutation_test(suite_dir, clean)
        killed = sum(r.killed for r in results)
        metrics.update(
            mutants=len(results),
            mutants_killed=killed,
            mutation_score=round(killed / len(results), 4) if results else 0.0,
        )
        details["mutants"] = [asdict(r) for r in results]
    return {"metrics": metrics, "details": details}
