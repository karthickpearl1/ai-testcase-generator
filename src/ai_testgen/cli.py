"""Command-line interface.

Exit codes: 0 = success / gate passed, 1 = quality gate failed, 2 = usage or configuration error.
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap
from pathlib import Path
from typing import Any

from ai_testgen import __version__
from ai_testgen.config import load_config
from ai_testgen.demo_api import MUTANTS
from ai_testgen.pipeline import generate_artefacts, run
from ai_testgen.providers import ProviderError
from ai_testgen.report import fmt, write_reports

EXIT_OK, EXIT_GATE_FAILED, EXIT_ERROR = 0, 1, 2


def _colour(text: str, code: str) -> str:
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def _print_metrics(metrics: dict[str, Any]) -> None:
    width = max(len(k) for k in metrics)
    for key, value in metrics.items():
        print(f"  {key:<{width}}  {fmt(key, value):>8}")


def cmd_generate(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    out = Path(args.out)
    result, coverage = generate_artefacts(config, out)
    summary = result.summary()
    print(
        f"Generated {summary['final_cases']} test cases "
        f"({summary['raw_cases']} proposed, {summary['rejected_cases']} rejected, "
        f"{summary['duplicates_removed']} duplicates removed)"
    )
    print(
        f"AC coverage {fmt('ac_coverage', coverage['summary']['ac_coverage'])}, "
        f"response coverage {fmt('response_coverage', coverage['summary']['response_coverage'])}"
    )
    print(f"Output: {out}/ (cases.json, exports/, tests/api/, tests/playwright/)")
    return EXIT_OK


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    out = Path(args.out)
    report = run(config, out, evaluate=not args.no_eval)
    print(f"{report['run']['name']}: {report['run']['provider']}/{report['run']['model']}\n")
    _print_metrics(report["metrics"])

    survivors = [m["name"] for m in report["evaluation"]["mutants"] if not m["killed"]]
    if survivors:
        print(f"\n  surviving mutants ({len(survivors)}):")
        print(
            textwrap.fill(
                ", ".join(survivors), width=88, initial_indent="    ", subsequent_indent="    "
            )
        )
    if report["evaluation"]["failing_tests"]:
        print(f"  failing generated tests: {', '.join(report['evaluation']['failing_tests'])}")

    paths = write_reports(report, out)
    if args.gate:
        print()
        for check in report["gate"]["checks"]:
            status = _colour("PASS", "32") if check["passed"] else _colour("FAIL", "31")
            print(f"  [{status}] {check['rule']:<4} {check['message']}")
        passed = report["gate"]["passed"]
        verdict = _colour("PASSED", "1;32") if passed else _colour("FAILED", "1;31")
        print(f"\nQuality gate: {verdict}")
    print(f"\nReports: {paths['html']}, {paths['markdown']}, {out / 'metrics.json'}")
    if args.gate and not report["gate"]["passed"]:
        return EXIT_GATE_FAILED
    return EXIT_OK


def cmd_demo_api(args: argparse.Namespace) -> int:
    if args.list_mutants:
        for name, description in MUTANTS.items():
            print(f"{name:<30} {description}")
        return EXIT_OK
    from ai_testgen.demo_api import serve

    serve(args.port, args.mutant)  # pragma: no cover - blocking
    return EXIT_OK  # pragma: no cover


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="testgen",
        description="Generate, evaluate and export test cases from user stories and OpenAPI specs.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="generate test cases, exports and test code")
    gen.add_argument("-c", "--config", default="testgen.yaml")
    gen.add_argument("-o", "--out", default="out")
    gen.set_defaults(func=cmd_generate)

    run_p = sub.add_parser("run", help="generate, execute, mutation-test and report")
    run_p.add_argument("-c", "--config", default="testgen.yaml")
    run_p.add_argument("-o", "--out", default="out")
    run_p.add_argument(
        "--gate", action="store_true", help="exit 1 if quality thresholds are not met"
    )
    run_p.add_argument(
        "--no-eval", action="store_true", help="skip executing the generated API tests"
    )
    run_p.set_defaults(func=cmd_run)

    demo = sub.add_parser("demo-api", help="serve the bundled Bookshop demo API")
    demo.add_argument("--port", type=int, default=8000)
    demo.add_argument("--mutant", choices=sorted(MUTANTS), help="inject one known bug")
    demo.add_argument("--list-mutants", action="store_true")
    demo.set_defaults(func=cmd_demo_api)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, ProviderError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
