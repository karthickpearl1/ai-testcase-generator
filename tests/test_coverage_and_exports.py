import csv
import io
import json

import pytest

from ai_testgen.coverage import coverage_map
from ai_testgen.exporters import to_csv, to_markdown, to_xray, to_zephyr
from ai_testgen.generation import generate
from ai_testgen.providers import MockProvider


@pytest.fixture(scope="module")
def generated(stories, endpoints):
    return generate(stories, endpoints, MockProvider())


def test_coverage_map(generated, stories, endpoints):
    coverage = coverage_map(generated.cases, stories, endpoints)
    summary = coverage["summary"]
    assert summary["ac_coverage"] == 1.0
    assert summary["endpoint_coverage"] == 1.0
    # 409 (out of stock) needs stateful setup the rules do not attempt; it shows up as a gap.
    assert summary["uncovered"] == ["POST /orders 409"]
    assert summary["response_coverage"] == pytest.approx(15 / 16, abs=1e-4)
    assert set(summary["by_type"]) == {"positive", "negative", "boundary", "security"}
    assert coverage["acceptance_criteria"]["US-101/AC2"]


def test_empty_coverage_is_vacuously_complete():
    assert coverage_map([], [], [])["summary"]["ac_coverage"] == 1.0


def test_csv_export(generated):
    rows = list(csv.DictReader(io.StringIO(to_csv(generated.cases))))
    assert len(rows) == len(generated.cases)
    api_row = next(r for r in rows if r["source"] == "POST /books")
    assert json.loads(api_row["test_data"])["method"] == "POST"
    assert rows[0]["steps"].startswith("1. ")


def test_markdown_export(generated):
    markdown = to_markdown(generated.cases)
    assert markdown.startswith("# Generated test cases")
    assert "## US-101" in markdown
    assert "## POST /orders" in markdown
    assert "\\|" not in markdown.split("\n")[0]


def test_xray_and_zephyr_exports(generated):
    case = generated.cases[0]
    xray = to_xray([case], "BOOK")[0]
    assert xray["testtype"] == "Manual"
    assert xray["fields"]["project"] == {"key": "BOOK"}
    assert xray["fields"]["summary"].startswith(case.id)
    assert xray["steps"][-1]["result"] == case.expected

    zephyr = to_zephyr([case], "BOOK")[0]
    assert zephyr["projectKey"] == "BOOK"
    assert zephyr["testScript"]["type"] == "STEP_BY_STEP"
    assert zephyr["testScript"]["steps"][-1]["expectedResult"] == case.expected

    api_case = next(c for c in generated.cases if c.request)
    first_step = to_xray([api_case], "BOOK")[0]["steps"][0]
    assert json.loads(first_step["data"])["path"] == api_case.request["path"]
