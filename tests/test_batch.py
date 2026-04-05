"""Tests for batch request support — sync and async."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.batch import AsyncBatchMixin, BatchMixin
from pisharp_piwebapi.exceptions import AuthenticationError, BatchError, ServerError

BASE = "https://piserver/piwebapi"

BATCH_RESPONSE = {
    "1": {"Status": 200, "Headers": {}, "Content": {"WebId": "P0ABC", "Name": "sinusoid"}},
    "2": {
        "Status": 200,
        "Headers": {},
        "Content": {"Timestamp": "2024-01-01T00:00:00Z", "Value": 1.0},
    },
}

BATCH_RESPONSE_PARTIAL_FAILURE = {
    "1": {"Status": 200, "Headers": {}, "Content": {"WebId": "P0ABC", "Name": "sinusoid"}},
    "2": {"Status": 404, "Headers": {}, "Content": {"Message": "Not found"}},
}

BATCH_RESPONSE_MULTI_FAILURE = {
    "1": {"Status": 404, "Headers": {}, "Content": {"Message": "Not found"}},
    "2": {"Status": 500, "Headers": {}, "Content": {"Message": "Server error"}},
}


class _SyncBatch(BatchMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncBatch(AsyncBatchMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync
# ===========================================================================


@respx.mock
def test_execute_batch_happy_path() -> None:
    """execute_batch returns the parsed response dict on 207."""
    respx.post(f"{BASE}/batch").mock(return_value=httpx.Response(207, json=BATCH_RESPONSE))

    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        result = batch.execute_batch(
            {
                "1": {"Method": "GET", "Resource": "/points?path=\\\\SERVER\\sinusoid"},
                "2": {"Method": "GET", "Resource": "/streams/{0}/value", "ParentIds": ["1"]},
            }
        )

    assert "1" in result
    assert "2" in result
    assert result["1"]["Status"] == 200
    assert result["1"]["Content"]["Name"] == "sinusoid"


@respx.mock
def test_execute_batch_server_error_raises() -> None:
    """execute_batch raises ServerError on 500."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )

    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        with pytest.raises(ServerError) as exc_info:
            batch.execute_batch({"1": {"Method": "GET", "Resource": "/points"}})

    assert exc_info.value.status_code == 500


@respx.mock
def test_execute_batch_auth_error_raises() -> None:
    """execute_batch raises AuthenticationError on 401."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        with pytest.raises(AuthenticationError) as exc_info:
            batch.execute_batch({"1": {"Method": "GET", "Resource": "/points"}})

    assert exc_info.value.status_code == 401


# ===========================================================================
# Async
# ===========================================================================


@respx.mock
async def test_async_execute_batch_happy_path() -> None:
    """Async execute_batch returns the parsed response dict on 207."""
    respx.post(f"{BASE}/batch").mock(return_value=httpx.Response(207, json=BATCH_RESPONSE))

    async with httpx.AsyncClient(base_url=BASE) as client:
        batch = _AsyncBatch(client)
        result = await batch.execute_batch(
            {
                "1": {"Method": "GET", "Resource": "/points?path=\\\\SERVER\\sinusoid"},
            }
        )

    assert "1" in result
    assert result["1"]["Content"]["Name"] == "sinusoid"


@respx.mock
async def test_async_execute_batch_server_error_raises() -> None:
    """Async execute_batch raises ServerError on 500."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        batch = _AsyncBatch(client)
        with pytest.raises(ServerError) as exc_info:
            await batch.execute_batch({"1": {"Method": "GET", "Resource": "/points"}})

    assert exc_info.value.status_code == 500


@respx.mock
async def test_async_execute_batch_auth_error_raises() -> None:
    """Async execute_batch raises AuthenticationError on 401."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        batch = _AsyncBatch(client)
        with pytest.raises(AuthenticationError) as exc_info:
            await batch.execute_batch({"1": {"Method": "GET", "Resource": "/points"}})

    assert exc_info.value.status_code == 401


# ===========================================================================
# Sub-request error detection (sync)
# ===========================================================================


@respx.mock
def test_execute_batch_partial_failure_raises_batch_error() -> None:
    """execute_batch raises BatchError when a sub-request fails."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(207, json=BATCH_RESPONSE_PARTIAL_FAILURE)
    )

    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        with pytest.raises(BatchError) as exc_info:
            batch.execute_batch(
                {"1": {"Method": "GET", "Resource": "/points"}, "2": {"Method": "GET", "Resource": "/missing"}},
            )

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0]["RequestId"] == "2"
    assert exc_info.value.errors[0]["Status"] == 404
    assert "2" in str(exc_info.value)


@respx.mock
def test_execute_batch_multi_failure_reports_all() -> None:
    """BatchError includes all failed sub-requests."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(207, json=BATCH_RESPONSE_MULTI_FAILURE)
    )

    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        with pytest.raises(BatchError) as exc_info:
            batch.execute_batch(
                {"1": {"Method": "GET", "Resource": "/a"}, "2": {"Method": "GET", "Resource": "/b"}},
            )

    assert len(exc_info.value.errors) == 2
    failed_ids = {e["RequestId"] for e in exc_info.value.errors}
    assert failed_ids == {"1", "2"}


@respx.mock
def test_execute_batch_raise_on_errors_false_returns_raw() -> None:
    """execute_batch with raise_on_errors=False returns raw data."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(207, json=BATCH_RESPONSE_PARTIAL_FAILURE)
    )

    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        result = batch.execute_batch(
            {"1": {"Method": "GET", "Resource": "/points"}, "2": {"Method": "GET", "Resource": "/missing"}},
            raise_on_errors=False,
        )

    assert result["2"]["Status"] == 404


@respx.mock
def test_execute_batch_all_success_no_error() -> None:
    """execute_batch does not raise when all sub-requests succeed."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(207, json=BATCH_RESPONSE)
    )

    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        result = batch.execute_batch(
            {"1": {"Method": "GET", "Resource": "/points"}, "2": {"Method": "GET", "Resource": "/value"}},
        )

    assert result["1"]["Status"] == 200
    assert result["2"]["Status"] == 200


# ===========================================================================
# Sub-request error detection (async)
# ===========================================================================


@respx.mock
async def test_async_execute_batch_partial_failure_raises() -> None:
    """Async execute_batch raises BatchError on sub-request failure."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(207, json=BATCH_RESPONSE_PARTIAL_FAILURE)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        batch = _AsyncBatch(client)
        with pytest.raises(BatchError) as exc_info:
            await batch.execute_batch(
                {"1": {"Method": "GET", "Resource": "/points"}, "2": {"Method": "GET", "Resource": "/missing"}},
            )

    assert len(exc_info.value.errors) == 1
    assert exc_info.value.errors[0]["RequestId"] == "2"


@respx.mock
async def test_async_execute_batch_raise_on_errors_false() -> None:
    """Async execute_batch with raise_on_errors=False returns raw data."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(207, json=BATCH_RESPONSE_PARTIAL_FAILURE)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        batch = _AsyncBatch(client)
        result = await batch.execute_batch(
            {"1": {"Method": "GET", "Resource": "/points"}, "2": {"Method": "GET", "Resource": "/missing"}},
            raise_on_errors=False,
        )

    assert result["2"]["Status"] == 404


# ===========================================================================
# Batch request validation (SSRF prevention)
# ===========================================================================


def test_batch_rejects_absolute_resource_url() -> None:
    """execute_batch rejects absolute URLs in Resource (SSRF prevention)."""
    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        with pytest.raises(ValueError, match="relative path"):
            batch.execute_batch(
                {"1": {"Method": "GET", "Resource": "https://evil.com/steal"}}
            )


def test_batch_rejects_invalid_method() -> None:
    """execute_batch rejects unexpected HTTP methods."""
    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        with pytest.raises(ValueError, match="invalid method"):
            batch.execute_batch(
                {"1": {"Method": "TRACE", "Resource": "/points"}}
            )


def test_batch_rejects_empty_resource() -> None:
    """execute_batch rejects empty Resource strings."""
    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        with pytest.raises(ValueError, match="relative path"):
            batch.execute_batch(
                {"1": {"Method": "GET", "Resource": ""}}
            )


async def test_async_batch_rejects_absolute_resource_url() -> None:
    """Async execute_batch rejects absolute URLs in Resource."""
    async with httpx.AsyncClient(base_url=BASE) as client:
        batch = _AsyncBatch(client)
        with pytest.raises(ValueError, match="relative path"):
            await batch.execute_batch(
                {"1": {"Method": "GET", "Resource": "https://evil.com/steal"}}
            )


async def test_async_batch_rejects_invalid_method() -> None:
    """Async execute_batch rejects unexpected HTTP methods."""
    async with httpx.AsyncClient(base_url=BASE) as client:
        batch = _AsyncBatch(client)
        with pytest.raises(ValueError, match="invalid method"):
            await batch.execute_batch(
                {"1": {"Method": "OPTIONS", "Resource": "/points"}}
            )
