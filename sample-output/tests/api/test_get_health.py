"""Generated API tests for GET /health (Health check).

Source: bookshop.yaml. Regenerate with `testgen generate` rather than editing by hand.
"""

import pytest


@pytest.mark.positive
def test_tc_033_succeeds_with_valid_input(api):
    """TC-033: Health check succeeds with valid input

    Traces: GET /health, GET /health 200
    """
    response = api.request(
        "GET",
        "/health",
    )
    assert response.status_code == 200, response.text
    body = response.json()
    for key in ("status",):
        assert key in body, f"response is missing {key!r}"
