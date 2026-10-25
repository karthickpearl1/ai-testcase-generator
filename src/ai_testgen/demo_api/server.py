"""Bookshop demo API, implemented with the standard library only.

It matches ``examples/openapi/bookshop.yaml``. Each entry in ``MUTANTS`` switches on one
deliberately injected bug, which is how the evaluation measures whether the generated tests
would actually catch real defects (a mutation score), not just whether they pass.
"""

from __future__ import annotations

import json
import re
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

DEMO_TOKEN = "demo-token"
FORMATS = ("hardback", "paperback", "ebook")

MUTANTS: dict[str, str] = {
    "title_max_length_unchecked": "POST /books accepts titles longer than 120 characters",
    "negative_price_accepted": "POST /books accepts a price below the 0.01 minimum",
    "price_type_unchecked": "POST /books does not type-check price (non-numbers cause a 500)",
    "create_returns_200": "POST /books returns 200 instead of 201",
    "quote_in_title_crashes": "POST /books fails with a 500 when the title contains a quote",
    "invalid_token_accepted": "Any bearer token is accepted, not just a valid one",
    "delete_without_auth": "DELETE /books/{bookId} does not require authentication",
    "missing_book_returns_500": "GET /books/{bookId} returns 500 instead of 404 for unknown ids",
    "book_response_missing_author": "GET /books/{bookId} omits the author field",
    "limit_upper_bound_ignored": "GET /books accepts limit values above 100",
    "quantity_off_by_one": "POST /orders accepts a quantity of 11",
    "stock_not_decremented": "POST /orders does not reduce stock",
    "out_of_stock_allowed": "POST /orders allows ordering more than the available stock",
}


class ValidationError(Exception):
    pass


def _seed_books() -> dict[int, dict[str, Any]]:
    return {
        1: {
            "id": 1,
            "title": "Jane Eyre",
            "author": "Charlotte Bronte",
            "price": 7.99,
            "stock": 50,
            "format": "paperback",
        },
        2: {
            "id": 2,
            "title": "North and South",
            "author": "Elizabeth Gaskell",
            "price": 9.5,
            "stock": 5,
            "format": "hardback",
        },
        3: {
            "id": 3,
            "title": "Middlemarch",
            "author": "George Eliot",
            "price": 6.0,
            "stock": 0,
            "format": "ebook",
        },
    }


class BookshopState:
    def __init__(self, mutant: str | None = None) -> None:
        if mutant is not None and mutant not in MUTANTS:
            raise ValueError(f"Unknown mutant '{mutant}'. Known: {', '.join(MUTANTS)}")
        self.mutant = mutant
        self.books = _seed_books()
        self.orders: dict[int, dict[str, Any]] = {}
        self.lock = threading.Lock()

    def bug(self, name: str) -> bool:
        return self.mutant == name


def _require_number(body: dict[str, Any], name: str, low: float, high: float, integer: bool) -> Any:
    value = body.get(name)
    allowed = (int,) if integer else (int, float)
    if isinstance(value, bool) or not isinstance(value, allowed):
        raise ValidationError(f"'{name}' must be {'an integer' if integer else 'a number'}")
    if not low <= value <= high:
        raise ValidationError(f"'{name}' must be between {low} and {high}")
    return value


def _require_string(body: dict[str, Any], name: str, max_length: int) -> str:
    value = body.get(name)
    if not isinstance(value, str):
        raise ValidationError(f"'{name}' must be a string")
    if not 1 <= len(value) <= max_length:
        raise ValidationError(f"'{name}' must be 1-{max_length} characters")
    return value


class Handler(BaseHTTPRequestHandler):
    state: BookshopState  # set per server in make_server()
    server_version = "BookshopDemo/1.0"

    # -- plumbing ---------------------------------------------------------------------------
    def log_message(self, format: str, *args: Any) -> None:  # silence request logging
        pass

    def _send(self, status: int, payload: Any = None) -> None:
        body = b"" if payload is None else json.dumps(payload).encode()
        self.send_response(status)
        if payload is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str) -> None:
        self._send(status, {"error": message})

    def _authorised(self) -> bool:
        header = self.headers.get("Authorization", "")
        if self.state.bug("invalid_token_accepted"):
            return header.startswith("Bearer ")
        return header == f"Bearer {DEMO_TOKEN}"

    def _json_body(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw or b"null")
        except json.JSONDecodeError:
            raise ValidationError("Body must be valid JSON") from None

    def _dispatch(self, method: str) -> None:
        url = urlparse(self.path)
        routes = (
            ("GET", r"/health", self.get_health),
            ("GET", r"/books", self.list_books),
            ("POST", r"/books", self.create_book),
            ("GET", r"/books/(?P<book_id>[^/]+)", self.get_book),
            ("DELETE", r"/books/(?P<book_id>[^/]+)", self.delete_book),
            ("POST", r"/orders", self.create_order),
        )
        for route_method, pattern, handler in routes:
            match = re.fullmatch(pattern, url.path)
            if match and route_method == method:
                try:
                    handler(query=parse_qs(url.query), **match.groupdict())
                except ValidationError as exc:
                    self._error(400, str(exc))
                except Exception as exc:  # what a real framework would turn into a 500
                    self._error(500, f"Internal server error: {type(exc).__name__}")
                return
        self._error(404, "Not found")

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def do_DELETE(self) -> None:
        self._dispatch("DELETE")

    # -- endpoints --------------------------------------------------------------------------
    def get_health(self, query: dict[str, list[str]]) -> None:
        self._send(200, {"status": "ok"})

    def list_books(self, query: dict[str, list[str]]) -> None:
        limit = 20
        if "limit" in query:
            try:
                limit = int(query["limit"][0])
            except ValueError:
                raise ValidationError("'limit' must be an integer") from None
            upper = 10**6 if self.state.bug("limit_upper_bound_ignored") else 100
            if not 1 <= limit <= upper:
                raise ValidationError("'limit' must be between 1 and 100")
        with self.state.lock:
            books = list(self.state.books.values())[:limit]
        self._send(200, books)

    def create_book(self, query: dict[str, list[str]]) -> None:
        if not self._authorised():
            return self._error(401, "Missing or invalid bearer token")
        body = self._json_body()
        if not isinstance(body, dict):
            raise ValidationError("Body must be a JSON object")
        max_title = 10**6 if self.state.bug("title_max_length_unchecked") else 120
        title = _require_string(body, "title", max_title)
        author = _require_string(body, "author", 80)
        if self.state.bug("price_type_unchecked"):
            price = body.get("price")
            if price is None:
                raise ValidationError("'price' is required")
            if price < 0.01:  # TypeError for strings, surfacing as a 500
                raise ValidationError("'price' must be at least 0.01")
        else:
            low = -(10**6) if self.state.bug("negative_price_accepted") else 0.01
            price = _require_number(body, "price", low, 1000, integer=False)
        stock = _require_number(body, "stock", 0, 10000, integer=True) if "stock" in body else 0
        book_format = body.get("format", "paperback")
        if book_format not in FORMATS:
            raise ValidationError(f"'format' must be one of {', '.join(FORMATS)}")
        if self.state.bug("quote_in_title_crashes") and "'" in title:
            raise RuntimeError("unescaped quote in SQL")

        with self.state.lock:
            book_id = max(self.state.books, default=0) + 1
            book = {
                "id": book_id,
                "title": title,
                "author": author,
                "price": price,
                "stock": stock,
                "format": book_format,
            }
            self.state.books[book_id] = book
        self._send(200 if self.state.bug("create_returns_200") else 201, book)

    def _book_id(self, raw: str) -> int:
        try:
            return int(raw)
        except ValueError:
            raise ValidationError("'bookId' must be an integer") from None

    def get_book(self, query: dict[str, list[str]], book_id: str) -> None:
        with self.state.lock:
            book = self.state.books.get(self._book_id(book_id))
        if book is None:
            if self.state.bug("missing_book_returns_500"):
                raise KeyError(book_id)
            return self._error(404, "Book not found")
        if self.state.bug("book_response_missing_author"):
            book = {k: v for k, v in book.items() if k != "author"}
        self._send(200, book)

    def delete_book(self, query: dict[str, list[str]], book_id: str) -> None:
        if not self.state.bug("delete_without_auth") and not self._authorised():
            return self._error(401, "Missing or invalid bearer token")
        with self.state.lock:
            removed = self.state.books.pop(self._book_id(book_id), None)
        if removed is None:
            return self._error(404, "Book not found")
        self._send(204)

    def create_order(self, query: dict[str, list[str]]) -> None:
        if not self._authorised():
            return self._error(401, "Missing or invalid bearer token")
        body = self._json_body()
        if not isinstance(body, dict):
            raise ValidationError("Body must be a JSON object")
        book_id = _require_number(body, "book_id", 1, 10**9, integer=True)
        max_quantity = 11 if self.state.bug("quantity_off_by_one") else 10
        quantity = _require_number(body, "quantity", 1, max_quantity, integer=True)
        with self.state.lock:
            book = self.state.books.get(book_id)
            if book is None:
                return self._error(404, "Book not found")
            if quantity > book["stock"] and not self.state.bug("out_of_stock_allowed"):
                return self._error(409, "Not enough stock")
            if not self.state.bug("stock_not_decremented"):
                book["stock"] -= quantity
            order_id = len(self.state.orders) + 1
            order = {
                "id": order_id,
                "book_id": book_id,
                "quantity": quantity,
                "total": round(book["price"] * quantity, 2),
            }
            self.state.orders[order_id] = order
        self._send(201, order)


def make_server(
    host: str = "127.0.0.1", port: int = 0, mutant: str | None = None
) -> ThreadingHTTPServer:
    state = BookshopState(mutant)
    handler = type("BoundHandler", (Handler,), {"state": state})
    return ThreadingHTTPServer((host, port), handler)


@contextmanager
def running_server(mutant: str | None = None) -> Iterator[str]:
    """Start a fresh server with seeded data on a free port; yield its base URL."""
    server = make_server(mutant=mutant)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def serve(port: int = 8000, mutant: str | None = None) -> None:  # pragma: no cover - blocking
    server = make_server(port=port, mutant=mutant)
    print(f"Bookshop demo API on http://127.0.0.1:{port} (mutant: {mutant or 'none'})")
    print(f"Use 'Authorization: Bearer {DEMO_TOKEN}' for secured endpoints. Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
