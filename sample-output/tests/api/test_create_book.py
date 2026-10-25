"""Generated API tests for POST /books (Add a book to the catalogue).

Source: bookshop.yaml. Regenerate with `testgen generate` rather than editing by hand.
"""

import pytest


@pytest.mark.positive
def test_tc_039_succeeds_with_valid_input(api):
    """TC-039: Add a book to the catalogue succeeds with valid input

    Traces: POST /books, POST /books 201
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "title", "author", "price", "stock", "format"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.negative
def test_tc_040_is_rejected_when_required_field_title_is_missing(api):
    """TC-040: Add a book to the catalogue is rejected when required field 'title' is missing

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.negative
def test_tc_041_is_rejected_when_title_has_the_wrong_type(api):
    """TC-041: Add a book to the catalogue is rejected when 'title' has the wrong type

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": 12345,
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.negative
def test_tc_042_is_rejected_when_required_field_author_is(api):
    """TC-042: Add a book to the catalogue is rejected when required field 'author' is missing

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.negative
def test_tc_043_is_rejected_when_author_has_the_wrong_type(api):
    """TC-043: Add a book to the catalogue is rejected when 'author' has the wrong type

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": 12345,
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.negative
def test_tc_044_is_rejected_when_required_field_price_is_missing(api):
    """TC-044: Add a book to the catalogue is rejected when required field 'price' is missing

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.negative
def test_tc_045_is_rejected_when_price_has_the_wrong_type(api):
    """TC-045: Add a book to the catalogue is rejected when 'price' has the wrong type

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": "not-a-number",
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.negative
def test_tc_046_is_rejected_when_format_is_not_an_allowed_value(api):
    """TC-046: Add a book to the catalogue is rejected when 'format' is not an allowed value

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 25,
            "format": "not-a-valid-option",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_047_title_at_minimum_length_1_is_accepted(api):
    """TC-047: Add a book to the catalogue: 'title' at minimum length (1) is accepted

    Traces: POST /books, POST /books 201
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "x",
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "title", "author", "price", "stock", "format"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.boundary
def test_tc_048_title_below_minimum_length_1_is_rejected(api):
    """TC-048: Add a book to the catalogue: 'title' below minimum length (1) is rejected

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "",
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_049_title_at_maximum_length_120_is_accepted(api):
    """TC-049: Add a book to the catalogue: 'title' at maximum length (120) is accepted

    Traces: POST /books, POST /books 201
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "x" * 120,
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "title", "author", "price", "stock", "format"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.boundary
def test_tc_050_title_above_maximum_length_120_is_rejected(api):
    """TC-050: Add a book to the catalogue: 'title' above maximum length (120) is rejected

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "x" * 121,
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_051_author_at_minimum_length_1_is_accepted(api):
    """TC-051: Add a book to the catalogue: 'author' at minimum length (1) is accepted

    Traces: POST /books, POST /books 201
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "x",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "title", "author", "price", "stock", "format"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.boundary
def test_tc_052_author_below_minimum_length_1_is_rejected(api):
    """TC-052: Add a book to the catalogue: 'author' below minimum length (1) is rejected

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_053_author_at_maximum_length_80_is_accepted(api):
    """TC-053: Add a book to the catalogue: 'author' at maximum length (80) is accepted

    Traces: POST /books, POST /books 201
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "x" * 80,
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "title", "author", "price", "stock", "format"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.boundary
def test_tc_054_author_above_maximum_length_80_is_rejected(api):
    """TC-054: Add a book to the catalogue: 'author' above maximum length (80) is rejected

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "x" * 81,
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_055_price_at_minimum_0_01_is_accepted(api):
    """TC-055: Add a book to the catalogue: 'price' at minimum (0.01) is accepted

    Traces: POST /books, POST /books 201
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 0.01,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "title", "author", "price", "stock", "format"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.boundary
def test_tc_056_price_below_minimum_0_01_is_rejected(api):
    """TC-056: Add a book to the catalogue: 'price' below minimum (0.01) is rejected

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 0.0,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_057_price_at_maximum_1000_is_accepted(api):
    """TC-057: Add a book to the catalogue: 'price' at maximum (1000) is accepted

    Traces: POST /books, POST /books 201
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 1000,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "title", "author", "price", "stock", "format"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.boundary
def test_tc_058_price_above_maximum_1000_is_rejected(api):
    """TC-058: Add a book to the catalogue: 'price' above maximum (1000) is rejected

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 1000.01,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_059_stock_at_minimum_0_is_accepted(api):
    """TC-059: Add a book to the catalogue: 'stock' at minimum (0) is accepted

    Traces: POST /books, POST /books 201
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 0,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "title", "author", "price", "stock", "format"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.boundary
def test_tc_060_stock_below_minimum_0_is_rejected(api):
    """TC-060: Add a book to the catalogue: 'stock' below minimum (0) is rejected

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": -1,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.boundary
def test_tc_061_stock_at_maximum_10000_is_accepted(api):
    """TC-061: Add a book to the catalogue: 'stock' at maximum (10000) is accepted

    Traces: POST /books, POST /books 201
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 10000,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    for key in ("id", "title", "author", "price", "stock", "format"):
        assert key in body, f"response is missing {key!r}"


@pytest.mark.boundary
def test_tc_062_stock_above_maximum_10000_is_rejected(api):
    """TC-062: Add a book to the catalogue: 'stock' above maximum (10000) is rejected

    Traces: POST /books, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 10001,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code == 400, response.text


@pytest.mark.security
def test_tc_063_is_refused_without_a_token(api):
    """TC-063: Add a book to the catalogue is refused without a token

    Traces: POST /books, POST /books 401
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
    )
    assert response.status_code == 401, response.text


@pytest.mark.security
def test_tc_064_is_refused_with_an_invalid_token(api):
    """TC-064: Add a book to the catalogue is refused with an invalid token

    Traces: POST /books, POST /books 401
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Wuthering Heights",
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="invalid",
    )
    assert response.status_code == 401, response.text


@pytest.mark.security
def test_tc_065_handles_an_injection_payload_in_title_without_a(api):
    """TC-065: Add a book to the catalogue handles an injection payload in 'title' without a server error

    Traces: POST /books, POST /books 201, POST /books 400
    """
    response = api.request(
        "POST",
        "/books",
        body={
            "title": "Robert'); DROP TABLE books;--",
            "author": "Emily Bronte",
            "price": 8.99,
            "stock": 25,
            "format": "paperback",
        },
        auth="valid",
    )
    assert response.status_code in (201, 400), response.text
