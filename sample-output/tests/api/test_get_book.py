"""Generated API tests for GET /books/{bookId} (Get a book by id).

Source: bookshop.yaml. Regenerate with `testgen generate` rather than editing by hand.
"""

import pytest


@pytest.mark.positive
def test_tc_066_succeeds_with_valid_input(api):
    """TC-066: Get a book by id succeeds with valid input

    Traces: GET /books/{bookId}, GET /books/{bookId} 200
    """
    response = api.request(
        "GET",
        "/books/{bookId}",
        path_params={"bookId": 1},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    for key in ("id", "title", "author", "price", "stock", "format"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.negative
def test_tc_067_returns_404_for_a_non_existent_bookid(api):
    """TC-067: Get a book by id returns 404 for a non-existent bookId

    Traces: GET /books/{bookId}, GET /books/{bookId} 404
    """
    response = api.request(
        "GET",
        "/books/{bookId}",
        path_params={"bookId": 999999},
    )
    assert response.status_code == 404, response.text
