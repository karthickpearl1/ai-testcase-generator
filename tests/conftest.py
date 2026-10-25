from __future__ import annotations

from pathlib import Path

import pytest

from ai_testgen.config import load_config
from ai_testgen.openapi import load_openapi
from ai_testgen.pipeline import load_inputs, run

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _no_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep a developer's local provider settings out of the tests."""
    monkeypatch.delenv("TESTGEN_PROVIDER", raising=False)


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def inputs():
    return load_inputs(load_config(ROOT / "testgen.yaml"))


@pytest.fixture(scope="session")
def stories(inputs):
    return inputs[0]


@pytest.fixture(scope="session")
def endpoints():
    return load_openapi(ROOT / "examples" / "openapi" / "bookshop.yaml")


@pytest.fixture(scope="session")
def endpoint_dicts(endpoints):
    return {e.id: e.to_prompt_dict() for e in endpoints}


@pytest.fixture(scope="session")
def baseline_run(tmp_path_factory):
    """One full baseline run (generation, execution and mutation testing) shared by tests."""
    out = tmp_path_factory.mktemp("baseline")
    return out, run(load_config(ROOT / "testgen.yaml"), out)
