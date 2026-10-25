"""YAML configuration with optional ``extends`` for candidate configs."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_PATH_KEYS = ("stories", "openapi")


@dataclass
class ProviderConfig:
    name: str = "mock"
    model: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class Config:
    name: str
    stories: Path | None
    openapi: Path | None
    provider: ProviderConfig
    project_key: str = "DEMO"
    execute_api_tests: bool = True
    mutation_testing: bool = True
    base_url: str | None = None
    gate_min: dict[str, float] = field(default_factory=dict)
    gate_max: dict[str, float] = field(default_factory=dict)
    source: Path | None = None


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_raw(path: Path, seen: tuple[Path, ...] = ()) -> dict[str, Any]:
    path = path.resolve()
    if path in seen:
        raise ValueError(f"Circular 'extends' in config: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    inputs = raw.get("inputs") or {}
    # Resolve paths against the file that declares them, so 'extends' works across folders.
    for key in _PATH_KEYS:
        if inputs.get(key):
            inputs[key] = str(path.parent / inputs[key])
    parent = raw.pop("extends", None)
    if parent:
        raw = _deep_merge(_read_raw(path.parent / parent, (*seen, path)), raw)
    return raw


def load_config(path: str | Path) -> Config:
    path = Path(path)
    raw = _read_raw(path)
    inputs = raw.get("inputs") or {}
    if not inputs.get("stories") and not inputs.get("openapi"):
        raise ValueError(f"Config {path} needs inputs.stories and/or inputs.openapi")

    provider_raw = raw.get("provider") or {}
    configured = provider_raw.get("name", "mock")
    override = os.environ.get("TESTGEN_PROVIDER")
    if override and override != configured:
        # Mock-only options (degradation knobs) must not be passed to a real provider.
        provider = ProviderConfig(name=override)
    else:
        provider = ProviderConfig(
            configured, provider_raw.get("model"), dict(provider_raw.get("options") or {})
        )

    evaluation = raw.get("evaluation") or {}
    gate = raw.get("gate") or {}
    return Config(
        name=raw.get("name", path.stem),
        stories=Path(inputs["stories"]) if inputs.get("stories") else None,
        openapi=Path(inputs["openapi"]) if inputs.get("openapi") else None,
        provider=provider,
        project_key=str(raw.get("project_key", "DEMO")),
        execute_api_tests=bool(evaluation.get("execute_api_tests", True)),
        mutation_testing=bool(evaluation.get("mutation_testing", True)),
        base_url=evaluation.get("base_url"),
        gate_min={k: float(v) for k, v in (gate.get("min") or {}).items()},
        gate_max={k: float(v) for k, v in (gate.get("max") or {}).items()},
        source=path,
    )
