"""Markdown and HTML reports for a generation + evaluation run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

PERCENT_METRICS = (
    "schema_validity",
    "ac_coverage",
    "endpoint_coverage",
    "response_coverage",
    "execution_pass_rate",
    "mutation_score",
)


def fmt(metric: str, value: Any) -> str:
    if value is None:
        return "-"
    if metric in PERCENT_METRICS:
        return f"{value * 100:.1f}%"
    if isinstance(value, float):
        return f"{value:,.1f}"
    return f"{value:,}"


def render_markdown(report: dict[str, Any]) -> str:
    run, metrics, gate = report["run"], report["metrics"], report["gate"]
    lines = [
        f"# Test generation report: {run['name']}",
        "",
        f"Provider `{run['provider']}` / model `{run['model']}`",
        "",
        f"**Quality gate: {'PASSED' if gate['passed'] else 'FAILED'}**",
        "",
    ]
    lines += [f"- :x: {c['message']}" for c in gate["checks"] if not c["passed"]]
    lines += ["", "| Metric | Value |", "|---|---:|"]
    lines += [f"| {k} | {fmt(k, v)} |" for k, v in metrics.items()]
    lines += ["", "Cases by type: " + ", ".join(f"{k} {v}" for k, v in report["by_type"].items())]
    if report["uncovered"]:
        lines += ["", "Not covered: " + ", ".join(f"`{u}`" for u in report["uncovered"])]
    survivors = [m for m in report["evaluation"]["mutants"] if not m["killed"]]
    if report["evaluation"]["mutants"]:
        lines += ["", f"## Surviving mutants ({len(survivors)})", ""]
        lines += [f"- `{m['name']}`: {m['description']}" for m in survivors] or ["None."]
    failing = report["evaluation"]["failing_tests"]
    if failing:
        lines += ["", f"## Generated tests failing against the API ({len(failing)})", ""]
        lines += [f"- {tc}: {msg}" for tc, msg in failing.items()]
    if report["rejected"]:
        lines += ["", f"## Rejected model output ({len(report['rejected'])})", ""]
        lines += [
            f"- {r['source']} / {r['title']}: {'; '.join(r['errors'])}" for r in report["rejected"]
        ]
    return "\n".join(lines) + "\n"


_env = Environment(
    loader=PackageLoader("ai_testgen", "report_templates"),
    autoescape=select_autoescape(["html", "j2"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_html(report: dict[str, Any], out_dir: Path) -> str:
    cases = json.loads((out_dir / "cases.json").read_text(encoding="utf-8"))["cases"]
    coverage = json.loads((out_dir / "coverage.json").read_text(encoding="utf-8"))
    return _env.get_template("report.html.j2").render(
        report=report, cases=cases, coverage=coverage, fmt=fmt
    )


def write_reports(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    paths = {"markdown": out_dir / "report.md", "html": out_dir / "report.html"}
    paths["markdown"].write_text(render_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_html(report, out_dir), encoding="utf-8")
    return paths
