"""Tests for custom exceptions and error-classification helpers."""

from __future__ import annotations

import httpx
import pytest

from pisharp_piwebapi.exceptions import (
    AuthenticationError,
    BatchError,
    NotFoundError,
    PIWebAPIError,
    RateLimitError,
    ServerError,
    classify_error,
    raise_for_response,
)


# ===========================================================================
# Exception model
# ===========================================================================


def test_base_exception() -> None:
    """PIWebAPIError stores status_code and body."""
    err = PIWebAPIError("test error", status_code=400, body={"Message": "bad"})
    assert str(err) == "test error"
    assert err.status_code == 400
    assert err.body == {"Message": "bad"}


def test_auth_error_inherits() -> None:
    """AuthenticationError is a PIWebAPIError."""
    err = AuthenticationError("unauthorized", status_code=401)
    assert isinstance(err, PIWebAPIError)
    assert err.status_code == 401


def test_not_found_error() -> None:
    """NotFoundError is a PIWebAPIError."""
    err = NotFoundError("not found", status_code=404)
    assert isinstance(err, PIWebAPIError)


def test_batch_error_with_errors_list() -> None:
    """BatchError stores the per-item errors list."""
    err = BatchError("partial failure", errors=[{"id": "1", "status": 404}])
    assert len(err.errors) == 1
    assert err.errors[0]["status"] == 404


# ===========================================================================
# classify_error
# ===========================================================================


def test_classify_401_returns_authentication_error() -> None:
    """classify_error maps 401 to AuthenticationError."""
    exc = classify_error(401, "Unauthorized", {})
    assert isinstance(exc, AuthenticationError)
    assert exc.status_code == 401


def test_classify_403_returns_authentication_error() -> None:
    """classify_error maps 403 to AuthenticationError."""
    exc = classify_error(403, "Forbidden", {})
    assert isinstance(exc, AuthenticationError)
    assert exc.status_code == 403


def test_classify_404_returns_not_found_error() -> None:
    """classify_error maps 404 to NotFoundError."""
    exc = classify_error(404, "Not found", {})
    assert isinstance(exc, NotFoundError)
    assert exc.status_code == 404


def test_classify_429_returns_rate_limit_error() -> None:
    """classify_error maps 429 to RateLimitError."""
    exc = classify_error(429, "Too many requests", {})
    assert isinstance(exc, RateLimitError)
    assert exc.status_code == 429


def test_classify_500_returns_server_error() -> None:
    """classify_error maps 500 to ServerError."""
    exc = classify_error(500, "Internal server error", {})
    assert isinstance(exc, ServerError)
    assert exc.status_code == 500


def test_classify_503_returns_server_error() -> None:
    """classify_error maps any 5xx to ServerError."""
    exc = classify_error(503, "Service unavailable", {})
    assert isinstance(exc, ServerError)
    assert exc.status_code == 503


def test_classify_400_returns_base_error() -> None:
    """classify_error maps unrecognised 4xx to base PIWebAPIError."""
    exc = classify_error(400, "Bad request", {})
    assert type(exc) is PIWebAPIError  # exactly the base class, not a subclass
    assert exc.status_code == 400


def test_classify_preserves_body() -> None:
    """classify_error stores the raw body on the exception."""
    body = {"Message": "detail", "Errors": []}
    exc = classify_error(404, "detail", body)
    assert exc.body == body


# ===========================================================================
# raise_for_response (sync)
# ===========================================================================


def test_raise_for_response_noop_on_200() -> None:
    """raise_for_response does not raise for a 200 response."""
    resp = httpx.Response(200, json={"WebId": "P01"})
    raise_for_response(resp)  # must not raise


def test_raise_for_response_noop_on_204() -> None:
    """raise_for_response does not raise for a 204 No Content response."""
    resp = httpx.Response(204)
    raise_for_response(resp)  # must not raise


def test_raise_for_response_raises_not_found_on_404() -> None:
    """raise_for_response raises NotFoundError on 404 with JSON body."""
    resp = httpx.Response(404, json={"Message": "Point not found"})
    with pytest.raises(NotFoundError) as exc_info:
        raise_for_response(resp)
    assert exc_info.value.status_code == 404
    assert str(exc_info.value) == "Point not found"


def test_raise_for_response_raises_auth_error_on_401() -> None:
    """raise_for_response raises AuthenticationError on 401."""
    resp = httpx.Response(401, json={"Message": "Unauthorized"})
    with pytest.raises(AuthenticationError) as exc_info:
        raise_for_response(resp)
    assert exc_info.value.status_code == 401


def test_raise_for_response_raises_server_error_on_500() -> None:
    """raise_for_response raises ServerError on 500."""
    resp = httpx.Response(500, json={"Message": "Internal error"})
    with pytest.raises(ServerError) as exc_info:
        raise_for_response(resp)
    assert exc_info.value.status_code == 500


def test_raise_for_response_handles_non_json_body() -> None:
    """raise_for_response stores the raw text when the body is not JSON."""
    resp = httpx.Response(500, text="Internal Server Error")
    with pytest.raises(ServerError) as exc_info:
        raise_for_response(resp)
    assert exc_info.value.body == "Internal Server Error"
    assert "500" in str(exc_info.value)


def test_raise_for_response_uses_message_field() -> None:
    """raise_for_response extracts 'Message' from the JSON body as the exception message."""
    resp = httpx.Response(404, json={"Message": "Specific error text"})
    with pytest.raises(NotFoundError) as exc_info:
        raise_for_response(resp)
    assert str(exc_info.value) == "Specific error text"
