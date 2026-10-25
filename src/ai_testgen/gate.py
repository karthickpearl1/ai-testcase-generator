"""Quality gate over the combined generation and evaluation metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Check:
    rule: str
    metric: str
    value: float | None
    threshold: float
    passed: bool
    message: str


def evaluate_gate(
    metrics: dict[str, Any], minimums: dict[str, float], maximums: dict[str, float]
) -> list[Check]:
    checks = []
    for rule, bounds in (("min", minimums), ("max", maximums)):
        for metric, bound in bounds.items():
            value = metrics.get(metric)
            if value is None:  # fail closed: a metric that was not produced cannot pass
                checks.append(Check(rule, metric, None, bound, False, f"{metric} was not measured"))
                continue
            ok = value >= bound if rule == "min" else value <= bound
            op = (">=" if ok else "<") if rule == "min" else ("<=" if ok else ">")
            checks.append(
                Check(rule, metric, value, bound, ok, f"{metric} {value:.4g} {op} {bound:g}")
            )
    return checks


def gate_passed(checks: list[Check]) -> bool:
    return all(c.passed for c in checks)


def checks_to_dicts(checks: list[Check]) -> list[dict[str, Any]]:
    return [asdict(c) for c in checks]
