"""Generated API tests for POST /orders (Place an order for a book).

Source: bookshop.yaml. Regenerate with `testgen generate` rather than editing by hand.
"""

import pytest


@pytest.mark.positive
def test_tc_072_succeeds_with_valid_input(api):
    """TC-072: Place an order for a book succeeds with valid input

    Traces: POST /orders, POST /orders 201
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": 1, "quantity": 2},
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "book_id", "quantity", "total"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.negative
def test_tc_073_is_rejected_when_required_field_book_id_is(api):
    """TC-073: Place an order for a book is rejected when required field 'book_id' is missing

    Traces: POST /orders, POST /orders 400
    """
    response = api.request(
        "POST",
        "/orders",
        body={"quantity": 2},
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.negative
def test_tc_074_is_rejected_when_book_id_has_the_wrong_type(api):
    """TC-074: Place an order for a book is rejected when 'book_id' has the wrong type

    Traces: POST /orders, POST /orders 400
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": "not-a-number", "quantity": 2},
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.negative
def test_tc_075_is_rejected_when_required_field_quantity_is(api):
    """TC-075: Place an order for a book is rejected when required field 'quantity' is missing

    Traces: POST /orders, POST /orders 400
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": 1},
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.negative
def test_tc_076_is_rejected_when_quantity_has_the_wrong_type(api):
    """TC-076: Place an order for a book is rejected when 'quantity' has the wrong type

    Traces: POST /orders, POST /orders 400
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": 1, "quantity": "not-a-number"},
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_077_book_id_below_minimum_1_is_rejected(api):
    """TC-077: Place an order for a book: 'book_id' below minimum (1) is rejected

    Traces: POST /orders, POST /orders 400
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": 0, "quantity": 2},
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_078_quantity_at_minimum_1_is_accepted(api):
    """TC-078: Place an order for a book: 'quantity' at minimum (1) is accepted

    Traces: POST /orders, POST /orders 201
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": 1, "quantity": 1},
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "book_id", "quantity", "total"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.boundary
def test_tc_079_quantity_below_minimum_1_is_rejected(api):
    """TC-079: Place an order for a book: 'quantity' below minimum (1) is rejected

    Traces: POST /orders, POST /orders 400
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": 1, "quantity": 0},
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_080_quantity_at_maximum_10_is_accepted(api):
    """TC-080: Place an order for a book: 'quantity' at maximum (10) is accepted

    Traces: POST /orders, POST /orders 201
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": 1, "quantity": 10},
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "book_id", "quantity", "total"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.boundary
def test_tc_081_quantity_above_maximum_10_is_rejected(api):
    """TC-081: Place an order for a book: 'quantity' above maximum (10) is rejected

    Traces: POST /orders, POST /orders 400
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": 1, "quantity": 11},
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.negative
def test_tc_082_returns_404_when_book_id_does_not_exist(api):
    """TC-082: Place an order for a book returns 404 when 'book_id' does not exist

    Traces: POST /orders, POST /orders 404
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": 999999, "quantity": 2},
        auth="valid",
    )
    assert response.status_code == 404, response.text


@pytest.mark.security
def test_tc_083_is_refused_without_a_token(api):
    """TC-083: Place an order for a book is refused without a token

    Traces: POST /orders, POST /orders 401
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": 1, "quantity": 2},
    )
    assert response.status_code == 401, response.text


@pytest.mark.security
def test_tc_084_is_refused_with_an_invalid_token(api):
    """TC-084: Place an order for a book is refused with an invalid token

    Traces: POST /orders, POST /orders 401
    """
    response = api.request(
        "POST",
        "/orders",
        body={"book_id": 1, "quantity": 2},
        auth="invalid",
    )
    assert response.status_code == 401, response.text
