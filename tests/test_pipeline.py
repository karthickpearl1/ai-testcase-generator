import json
import runpy
import sys

import pytest

from ai_testgen.cli import EXIT_ERROR, EXIT_GATE_FAILED, EXIT_OK, main
from ai_testgen.config import load_config
from ai_testgen.evaluation import evaluate_suite, run_suite
from ai_testgen.gate import evaluate_gate, gate_passed
from ai_testgen.report import fmt, render_markdown


def test_baseline_run_metrics(baseline_run):
    _, report = baseline_run
    metrics = report["metrics"]
    assert metrics["schema_validity"] == 1.0
    assert metrics["ac_coverage"] == 1.0
    assert metrics["execution_pass_rate"] == 1.0
    assert metrics["api_tests_executed"] == metrics["api_cases"]
    assert report["gate"]["passed"]
    survivors = {m["name"] for m in report["evaluation"]["mutants"] if not m["killed"]}
    # Neither survivor is reachable by a stateless request/response test: that is the point.
    assert survivors == {"stock_not_decremented", "out_of_stock_allowed"}


def test_baseline_artefacts(baseline_run):
    out, _ = baseline_run
    for name in (
        "cases.json",
        "coverage.json",
        "metrics.json",
        "exports/xray.json",
        "exports/zephyr.json",
        "exports/test-cases.csv",
        "exports/test-cases.md",
        "tests/api/conftest.py",
    ):
        assert (out / name).exists(), name
    assert len(list((out / "tests" / "playwright").glob("*.spec.ts"))) == 3


def test_run_suite_reports_failures(baseline_run, tmp_path):
    out, _ = baseline_run
    suite = out / "tests" / "api"
    # Nothing listens on this port, so every test fails with a connection error.
    run = run_suite(suite, "http://127.0.0.1:9")
    assert not run.passed
    assert set(run.failures) == set(run.outcomes)

    external = evaluate_suite(suite, base_url="http://127.0.0.1:9")
    assert external["metrics"]["execution_pass_rate"] == 0.0
    assert "mutation_score" not in external["metrics"]

    with pytest.raises(RuntimeError, match="no results"):
        run_suite(tmp_path / "missing", "http://127.0.0.1:9")


def test_gate_fails_closed():
    checks = evaluate_gate({"a": 0.5, "b": 3}, {"a": 0.8, "missing": 1}, {"b": 2})
    assert [c.passed for c in checks] == [False, False, False]
    assert "not measured" in checks[1].message
    assert not gate_passed(checks)
    assert gate_passed(evaluate_gate({"a": 1}, {"a": 0.5}, {}))


def test_fmt():
    assert fmt("mutation_score", 0.8462) == "84.6%"
    assert fmt("final_cases", 1234) == "1,234"
    assert fmt("x", 2.25) == "2.2"
    assert fmt("x", None) == "-"


def test_markdown_report(baseline_run):
    _, report = baseline_run
    markdown = render_markdown(report)
    assert "**Quality gate: PASSED**" in markdown
    assert "## Surviving mutants (2)" in markdown
    assert "`POST /orders 409`" in markdown


@pytest.fixture
def in_repo(root, monkeypatch):
    monkeypatch.chdir(root)


def test_cli_noisy_model_fails_the_gate(in_repo, tmp_path, capsys):
    code = main(["run", "-c", "configs/noisy-model.yaml", "-o", str(tmp_path), "--gate"])
    assert code == EXIT_GATE_FAILED
    out = capsys.readouterr().out
    assert "Quality gate: FAILED" in out
    report = json.loads((tmp_path / "metrics.json").read_text())
    # Every weak test passes, yet most injected bugs go unnoticed.
    assert report["metrics"]["execution_pass_rate"] == 1.0
    assert report["metrics"]["mutation_score"] < 0.5
    assert report["rejected"]
    html = (tmp_path / "report.html").read_text()
    assert "Rejected model output" in html
    assert "SURVIVED" in html


def test_cli_generate_and_no_eval(in_repo, tmp_path, capsys):
    assert main(["generate", "-o", str(tmp_path / "gen")]) == EXIT_OK
    assert "Generated" in capsys.readouterr().out
    # Without execution the gate cannot see pass rate or mutation score, so it fails closed.
    assert main(["run", "--no-eval", "--gate", "-o", str(tmp_path / "ne")]) == EXIT_GATE_FAILED
    assert main(["run", "--no-eval", "-o", str(tmp_path / "ne2")]) == EXIT_OK


def test_cli_list_mutants_and_errors(in_repo, tmp_path, capsys):
    assert main(["demo-api", "--list-mutants"]) == EXIT_OK
    assert "quantity_off_by_one" in capsys.readouterr().out
    assert main(["run", "-c", "missing.yaml"]) == EXIT_ERROR
    empty = tmp_path / "empty.yaml"
    empty.write_text("name: x\n")
    assert main(["generate", "-c", str(empty)]) == EXIT_ERROR


def test_module_entry_point(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["testgen", "--version"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("ai_testgen", run_name="__main__")
    assert exc.value.code == 0


def test_config_extends_and_env_override(root, monkeypatch):
    noisy = load_config(root / "configs" / "noisy-model.yaml")
    assert noisy.name == "noisy-model"
    assert noisy.openapi == root / "examples" / "openapi" / "bookshop.yaml"
    assert noisy.provider.options["weak_assertions"] is True
    assert noisy.gate_min["mutation_score"] == 0.75
    monkeypatch.setenv("TESTGEN_PROVIDER", "bedrock")
    overridden = load_config(root / "configs" / "noisy-model.yaml")
    assert overridden.provider.name == "bedrock"
    assert overridden.provider.options == {}


def test_config_circular_extends(tmp_path):
    (tmp_path / "a.yaml").write_text("extends: b.yaml\n")
    (tmp_path / "b.yaml").write_text("extends: a.yaml\n")
    with pytest.raises(ValueError, match="Circular"):
        load_config(tmp_path / "a.yaml")


def test_single_story_file_input(tmp_path, root):
    from ai_testgen.pipeline import load_inputs

    config_path = tmp_path / "c.yaml"
    story = root / "examples" / "stories" / "US-101-basket.md"
    config_path.write_text(f"inputs:\n  stories: {story}\n")
    stories, endpoints = load_inputs(load_config(config_path))
    assert [s.id for s in stories] == ["US-101"]
    assert endpoints == []
