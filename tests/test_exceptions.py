"""Tests for custom exceptions."""

from pisharp_piwebapi.exceptions import (
    AuthenticationError,
    BatchError,
    NotFoundError,
    PIWebAPIError,
)


def test_base_exception():
    err = PIWebAPIError("test error", status_code=400, body={"Message": "bad"})
    assert str(err) == "test error"
    assert err.status_code == 400
    assert err.body == {"Message": "bad"}


def test_auth_error_inherits():
    err = AuthenticationError("unauthorized", status_code=401)
    assert isinstance(err, PIWebAPIError)
    assert err.status_code == 401


def test_not_found_error():
    err = NotFoundError("not found", status_code=404)
    assert isinstance(err, PIWebAPIError)


def test_batch_error_with_errors_list():
    err = BatchError("partial failure", errors=[{"id": "1", "status": 404}])
    assert len(err.errors) == 1
    assert err.errors[0]["status"] == 404
