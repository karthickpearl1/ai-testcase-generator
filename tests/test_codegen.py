import ast

import pytest

from ai_testgen.codegen import py_literal, write_playwright_specs, write_pytest_suite
from ai_testgen.codegen.pytest_api import function_name, slug
from ai_testgen.generation import generate
from ai_testgen.models import TestCase
from ai_testgen.providers import MockProvider


@pytest.mark.parametrize(
    ("value", "literal"),
    [
        ("x" * 121, '"x" * 121'),
        ("short", '"short"'),
        ('He said "hi"', '"He said \\"hi\\""'),
        (True, "True"),
        (None, "None"),
        (8.99, "8.99"),
        ([1, "a"], '[1, "a"]'),
        ({"a": {"b": False}}, '{"a": {"b": False}}'),
    ],
    ids=["long-string", "string", "quotes", "bool", "none", "float", "list", "dict"],
)
def test_py_literal(value, literal):
    assert py_literal(value) == literal
    assert eval(literal) == value  # trusted input: literals built by the test itself


def test_py_literal_rejects_unknown_types():
    with pytest.raises(TypeError):
        py_literal({1, 2})


def test_slug_and_function_names():
    assert (
        slug("Add a book: 'title' above maximum (120)!", limit=30)
        == "add_a_book_title_above_maximum"
    )
    assert slug("!!!") == "case"
    case = TestCase(
        "List books succeeds",
        "positive",
        "high",
        ["s"],
        "e",
        ["t"],
        "openapi",
        "GET /books",
        id="TC-007",
    )
    assert function_name(case, "List books") == "test_tc_007_succeeds"


@pytest.fixture(scope="module")
def generated(stories, endpoints):
    return generate(stories, endpoints, MockProvider())


def test_pytest_suite_is_valid_python(tmp_path, generated, endpoints):
    modules = write_pytest_suite(generated.cases, endpoints, tmp_path, "bookshop.yaml")
    assert len(modules) == len(endpoints)
    assert (tmp_path / "conftest.py").exists()
    assert "markers" in (tmp_path / "pytest.ini").read_text()
    for module in [*modules, tmp_path / "conftest.py"]:
        ast.parse(module.read_text())
    source = (tmp_path / "test_create_book.py").read_text()
    assert 'body={"title": "x" * 121' in source.replace("\n", "") or '"x" * 121' in source
    assert "@pytest.mark.security" in source
    assert "assert response.status_code in (201, 400), response.text" in source


def test_playwright_skeletons(tmp_path, generated, stories):
    specs = write_playwright_specs(generated.cases, stories, tmp_path)
    assert [p.name for p in specs] == [
        "us-101-add-a-book-to-the-basket.spec.ts",
        "us-102-register-an-account.spec.ts",
        "us-103-view-order-history.spec.ts",
    ]
    text = specs[0].read_text()
    assert text.startswith("import { test, expect } from '@playwright/test';")
    assert 'test.describe("US-101: Add a book to the basket"' in text
    assert 'test.step("Given I am viewing a book that is in stock"' in text
    assert 'test.step("I click \\"Add to basket\\""' in text
    assert 'test.step("Then the basket count increases by 1"' in text
    assert "test.fixme(" in text
    assert text.count("test.fixme(") == sum(c.source_ref == "US-101" for c in generated.cases)


def test_no_files_for_sources_without_cases(tmp_path, stories, endpoints):
    assert write_pytest_suite([], endpoints, tmp_path / "api", "x") == []
    assert write_playwright_specs([], stories, tmp_path / "pw") == []
