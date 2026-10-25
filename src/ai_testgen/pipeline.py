"""End-to-end orchestration: inputs -> generation -> artefacts -> evaluation -> gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_testgen import __version__
from ai_testgen.codegen import write_playwright_specs, write_pytest_suite
from ai_testgen.config import Config
from ai_testgen.coverage import coverage_map
from ai_testgen.evaluation import evaluate_suite
from ai_testgen.exporters import to_csv, to_markdown, to_xray, to_zephyr
from ai_testgen.gate import checks_to_dicts, evaluate_gate, gate_passed
from ai_testgen.generation import GenerationResult, generate
from ai_testgen.models import Endpoint, UserStory
from ai_testgen.openapi import load_openapi
from ai_testgen.providers import create_provider
from ai_testgen.stories import load_stories


def _dump(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_inputs(config: Config) -> tuple[list[UserStory], list[Endpoint]]:
    stories: list[UserStory] = []
    if config.stories:
        if config.stories.is_dir():
            files = [*config.stories.glob("*.md"), *config.stories.glob("*.feature")]
        else:
            files = [config.stories]
        stories = load_stories([f for f in files if f.name.lower() != "readme.md"])
    endpoints = load_openapi(config.openapi) if config.openapi else []
    return stories, endpoints


def generate_artefacts(config: Config, out_dir: Path) -> tuple[GenerationResult, dict[str, Any]]:
    """Generate cases and write every artefact (cases, exports, test code) into ``out_dir``."""
    stories, endpoints = load_inputs(config)
    provider = create_provider(
        config.provider.name, config.provider.model, **config.provider.options
    )
    result = generate(stories, endpoints, provider)
    coverage = coverage_map(result.cases, stories, endpoints)

    _dump(
        {"provider": provider.name, "model": provider.model, **result.to_dict()},
        out_dir / "cases.json",
    )
    _dump(coverage, out_dir / "coverage.json")
    exports = out_dir / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    (exports / "test-cases.csv").write_text(to_csv(result.cases), encoding="utf-8")
    (exports / "test-cases.md").write_text(to_markdown(result.cases), encoding="utf-8")
    _dump(to_xray(result.cases, config.project_key), exports / "xray.json")
    _dump(to_zephyr(result.cases, config.project_key), exports / "zephyr.json")

    spec_name = config.openapi.name if config.openapi else "(none)"
    write_pytest_suite(result.cases, endpoints, out_dir / "tests" / "api", spec_name)
    specs = write_playwright_specs(result.cases, stories, out_dir / "tests" / "playwright")
    coverage["summary"]["playwright_specs"] = len(specs)
    return result, coverage


def run(config: Config, out_dir: Path, *, evaluate: bool = True) -> dict[str, Any]:
    result, coverage = generate_artefacts(config, out_dir)
    generation = result.summary()
    cov = coverage["summary"]
    metrics: dict[str, Any] = {
        **{
            k: generation[k]
            for k in (
                "raw_cases",
                "rejected_cases",
                "schema_validity",
                "duplicates_removed",
                "final_cases",
                "api_cases",
            )
        },
        "story_cases": generation["final_cases"] - generation["api_cases"],
        "playwright_specs": cov["playwright_specs"],
        "ac_coverage": cov["ac_coverage"],
        "endpoint_coverage": cov["endpoint_coverage"],
        "response_coverage": cov["response_coverage"],
        "model_calls": generation["model_calls"],
        "input_tokens": generation["input_tokens"],
        "output_tokens": generation["output_tokens"],
    }

    evaluation: dict[str, Any] = {"failing_tests": {}, "mutants": []}
    if evaluate and config.execute_api_tests and metrics["api_cases"]:
        outcome = evaluate_suite(
            out_dir / "tests" / "api", base_url=config.base_url, mutation=config.mutation_testing
        )
        metrics.update(outcome["metrics"])
        evaluation = outcome["details"]

    checks = evaluate_gate(metrics, config.gate_min, config.gate_max)
    report = {
        "run": {
            "name": config.name,
            "config": str(config.source) if config.source else None,
            "provider": config.provider.name,
            "model": json.loads((out_dir / "cases.json").read_text())["model"],
            "version": __version__,
        },
        "metrics": metrics,
        "by_type": cov["by_type"],
        "uncovered": cov["uncovered"],
        "gate": {"passed": gate_passed(checks), "checks": checks_to_dicts(checks)},
        "evaluation": evaluation,
        "rejected": [r.__dict__ for r in result.rejected],
        "duplicates": [d.__dict__ for d in result.duplicates],
    }
    _dump(report, out_dir / "metrics.json")
    return report
