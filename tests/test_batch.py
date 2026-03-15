"""Tests for batch request support — sync and async."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.batch import AsyncBatchMixin, BatchMixin

BASE = "https://piserver/piwebapi"

BATCH_RESPONSE = {
    "1": {"Status": 200, "Headers": {}, "Content": {"WebId": "P0ABC", "Name": "sinusoid"}},
    "2": {"Status": 200, "Headers": {}, "Content": {"Timestamp": "2024-01-01T00:00:00Z", "Value": 1.0}},
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
    """execute_batch raises on 500."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )

    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        with pytest.raises(httpx.HTTPStatusError):
            batch.execute_batch({"1": {"Method": "GET", "Resource": "/points"}})


@respx.mock
def test_execute_batch_auth_error_raises() -> None:
    """execute_batch raises on 401."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    with httpx.Client(base_url=BASE) as client:
        batch = _SyncBatch(client)
        with pytest.raises(httpx.HTTPStatusError):
            batch.execute_batch({"1": {"Method": "GET", "Resource": "/points"}})


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
    """Async execute_batch raises on 500."""
    respx.post(f"{BASE}/batch").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        batch = _AsyncBatch(client)
        with pytest.raises(httpx.HTTPStatusError):
            await batch.execute_batch({"1": {"Method": "GET", "Resource": "/points"}})
