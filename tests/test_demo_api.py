import json
import urllib.error
import urllib.request

import pytest

from ai_testgen.demo_api import DEMO_TOKEN, MUTANTS, running_server
from ai_testgen.demo_api.server import BookshopState

AUTH = {"Authorization": f"Bearer {DEMO_TOKEN}"}
BOOK = {"title": "Persuasion", "author": "Jane Austen", "price": 5.5}


def call(base, method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=5) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"null")


@pytest.fixture(scope="module")
def api():
    with running_server() as url:
        yield url


@pytest.mark.parametrize(
    ("method", "path", "body", "headers", "status"),
    [
        ("GET", "/health", None, None, 200),
        ("GET", "/books?limit=2", None, None, 200),
        ("GET", "/books?limit=0", None, None, 400),
        ("GET", "/books?limit=abc", None, None, 400),
        ("GET", "/books/1", None, None, 200),
        ("GET", "/books/abc", None, None, 400),
        ("GET", "/books/999", None, None, 404),
        ("POST", "/books", BOOK, AUTH, 201),
        ("POST", "/books", BOOK, None, 401),
        ("POST", "/books", {**BOOK, "price": "cheap"}, AUTH, 400),
        ("POST", "/books", {**BOOK, "format": "scroll"}, AUTH, 400),
        ("POST", "/books", {**BOOK, "stock": -1}, AUTH, 400),
        ("POST", "/books", ["not", "an", "object"], AUTH, 400),
        ("POST", "/orders", {"book_id": 1, "quantity": 1}, AUTH, 201),
        ("POST", "/orders", {"book_id": 3, "quantity": 1}, AUTH, 409),
        ("POST", "/orders", {"book_id": 999, "quantity": 1}, AUTH, 404),
        ("POST", "/orders", {"book_id": 1, "quantity": 11}, AUTH, 400),
        ("POST", "/orders", None, None, 401),
        ("DELETE", "/books/999", None, AUTH, 404),
        ("GET", "/nowhere", None, None, 404),
    ],
)
def test_demo_api_contract(api, method, path, body, headers, status):
    assert call(api, method, path, body, headers)[0] == status


def test_listing_and_ordering_update_state(api):
    status, books = call(api, "GET", "/books?limit=1")
    assert status == 200
    assert len(books) == 1
    stock_before = call(api, "GET", "/books/2")[1]["stock"]
    assert call(api, "POST", "/orders", {"book_id": 2, "quantity": 2}, AUTH)[1]["total"] == 19.0
    assert call(api, "GET", "/books/2")[1]["stock"] == stock_before - 2


def test_invalid_json_body(api):
    request = urllib.request.Request(
        api + "/books", data=b"{nope", method="POST", headers={**AUTH, "Content-Length": "5"}
    )
    with pytest.raises(urllib.error.HTTPError) as err:
        urllib.request.urlopen(request, timeout=5)
    assert err.value.code == 400


def test_unknown_mutant():
    with pytest.raises(ValueError, match="Unknown mutant"):
        BookshopState("nope")


# One request per mutant that behaves differently from the correct API.
MUTANT_PROBES = {
    "title_max_length_unchecked": ("POST", "/books", {**BOOK, "title": "x" * 121}, AUTH, 201),
    "negative_price_accepted": ("POST", "/books", {**BOOK, "price": -5}, AUTH, 201),
    "price_type_unchecked": ("POST", "/books", {**BOOK, "price": "cheap"}, AUTH, 500),
    "create_returns_200": ("POST", "/books", BOOK, AUTH, 200),
    "quote_in_title_crashes": ("POST", "/books", {**BOOK, "title": "O'Brien"}, AUTH, 500),
    "invalid_token_accepted": ("POST", "/books", BOOK, {"Authorization": "Bearer nope"}, 201),
    "delete_without_auth": ("DELETE", "/books/3", None, None, 204),
    "missing_book_returns_500": ("GET", "/books/999", None, None, 500),
    "limit_upper_bound_ignored": ("GET", "/books?limit=500", None, None, 200),
    "quantity_off_by_one": ("POST", "/orders", {"book_id": 1, "quantity": 11}, AUTH, 201),
    "out_of_stock_allowed": ("POST", "/orders", {"book_id": 3, "quantity": 1}, AUTH, 201),
}


@pytest.mark.parametrize("mutant", sorted(MUTANT_PROBES))
def test_each_mutant_changes_behaviour(mutant):
    method, path, body, headers, status = MUTANT_PROBES[mutant]
    with running_server(mutant=mutant) as url:
        assert call(url, method, path, body, headers)[0] == status
    with running_server() as url:
        assert call(url, method, path, body, headers)[0] != status


def test_state_mutants():
    with running_server(mutant="book_response_missing_author") as url:
        assert "author" not in call(url, "GET", "/books/1")[1]
    with running_server(mutant="stock_not_decremented") as url:
        call(url, "POST", "/orders", {"book_id": 2, "quantity": 2}, AUTH)
        assert call(url, "GET", "/books/2")[1]["stock"] == 5
    assert len(MUTANTS) == len(MUTANT_PROBES) + 2
