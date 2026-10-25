"""Generated API tests for GET /books (List books).

Source: bookshop.yaml. Regenerate with `testgen generate` rather than editing by hand.
"""

import pytest


@pytest.mark.positive
def test_tc_034_succeeds_with_valid_input(api):
    """TC-034: List books succeeds with valid input

    Traces: GET /books, GET /books 200
    """
    response = api.request(
        "GET",
        "/books",
    )
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


@pytest.mark.boundary
def test_tc_035_query_limit_at_minimum_1_is_accepted(api):
    """TC-035: List books: query limit at minimum (1) is accepted

    Traces: GET /books, GET /books 200
    """
    response = api.request(
        "GET",
        "/books",
        query={"limit": 1},
    )
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


@pytest.mark.boundary
def test_tc_036_query_limit_below_minimum_1_is_rejected(api):
    """TC-036: List books: query limit below minimum (1) is rejected

    Traces: GET /books, GET /books 400
    """
    response = api.request(
        "GET",
        "/books",
        query={"limit": 0},
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_037_query_limit_at_maximum_100_is_accepted(api):
    """TC-037: List books: query limit at maximum (100) is accepted

    Traces: GET /books, GET /books 200
    """
    response = api.request(
        "GET",
        "/books",
        query={"limit": 100},
    )
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


@pytest.mark.boundary
def test_tc_038_query_limit_above_maximum_100_is_rejected(api):
    """TC-038: List books: query limit above maximum (100) is rejected

    Traces: GET /books, GET /books 400
    """
    response = api.request(
        "GET",
        "/books",
        query={"limit": 101},
    )
    assert response.status_code == 400, response.text
