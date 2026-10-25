"""Generated API tests for DELETE /books/{bookId} (Remove a book from the catalogue).

Source: bookshop.yaml. Regenerate with `testgen generate` rather than editing by hand.
"""

import pytest


@pytest.mark.positive
def test_tc_068_succeeds_with_valid_input(api):
    """TC-068: Remove a book from the catalogue succeeds with valid input

    Traces: DELETE /books/{bookId}, DELETE /books/{bookId} 204
    """
    response = api.request(
        "DELETE",
        "/books/{bookId}",
        path_params={"bookId": 2},
        auth="valid",
    )
    assert response.status_code == 204, response.text


@pytest.mark.negative
def test_tc_069_returns_404_for_a_non_existent_bookid(api):
    """TC-069: Remove a book from the catalogue returns 404 for a non-existent bookId

    Traces: DELETE /books/{bookId}, DELETE /books/{bookId} 404
    """
    response = api.request(
        "DELETE",
        "/books/{bookId}",
        path_params={"bookId": 999999},
        auth="valid",
    )
    assert response.status_code == 404, response.text


@pytest.mark.security
def test_tc_070_is_refused_without_a_token(api):
    """TC-070: Remove a book from the catalogue is refused without a token

    Traces: DELETE /books/{bookId}, DELETE /books/{bookId} 401
    """
    response = api.request(
        "DELETE",
        "/books/{bookId}",
        path_params={"bookId": 2},
    )
    assert response.status_code == 401, response.text


@pytest.mark.security
def test_tc_071_is_refused_with_an_invalid_token(api):
    """TC-071: Remove a book from the catalogue is refused with an invalid token

    Traces: DELETE /books/{bookId}, DELETE /books/{bookId} 401
    """
    response = api.request(
        "DELETE",
        "/books/{bookId}",
        path_params={"bookId": 2},
        auth="invalid",
    )
    assert response.status_code == 401, response.text
