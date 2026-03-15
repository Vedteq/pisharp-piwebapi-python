"""Tests for Streams/Values resource — sync and async."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest
import respx

from pisharp_piwebapi.models import StreamValue, StreamValues
from pisharp_piwebapi.values import AsyncStreamsMixin, StreamsMixin

BASE = "https://piserver/piwebapi"
WEB_ID = "F1AbEDFoo123"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

VALUE_PAYLOAD = {
    "Timestamp": "2024-06-01T12:00:00Z",
    "Value": 3.14,
    "UnitsAbbreviation": "degC",
    "Good": True,
    "Questionable": False,
    "Substituted": False,
    "Annotated": False,
}

RECORDED_PAYLOAD = {
    "WebId": WEB_ID,
    "Name": "sinusoid",
    "Path": "",
    "Items": [
        {
            "Timestamp": "2024-06-01T11:00:00Z",
            "Value": 1.0,
            "Good": True,
        },
        {
            "Timestamp": "2024-06-01T12:00:00Z",
            "Value": 2.0,
            "Good": True,
        },
    ],
    "UnitsAbbreviation": "degC",
    "Links": {},
}


# ---------------------------------------------------------------------------
# Sync helpers
# ---------------------------------------------------------------------------


class _SyncStreams(StreamsMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------


class _AsyncStreams(AsyncStreamsMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_value
# ===========================================================================


@respx.mock
def test_get_value_happy_path() -> None:
    """get_value returns a StreamValue with correct fields."""
    respx.get(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(200, json=VALUE_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        val = streams.get_value(WEB_ID)

    assert isinstance(val, StreamValue)
    assert val.value == pytest.approx(3.14)
    assert val.units_abbreviation == "degC"
    assert val.good is True
    assert isinstance(val.timestamp, datetime)
    assert val.timestamp.tzinfo is not None


@respx.mock
def test_get_value_404_raises() -> None:
    """get_value raises on 404."""
    respx.get(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        with pytest.raises(httpx.HTTPStatusError):
            streams.get_value(WEB_ID)


# ===========================================================================
# Sync — get_recorded
# ===========================================================================


@respx.mock
def test_get_recorded_happy_path() -> None:
    """get_recorded returns a StreamValues collection."""
    respx.get(f"{BASE}/streams/{WEB_ID}/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        vals = streams.get_recorded(WEB_ID, start_time="-1h", end_time="*")

    assert isinstance(vals, StreamValues)
    assert len(vals) == 2
    assert vals.items[0].value == pytest.approx(1.0)
    assert vals.items[1].value == pytest.approx(2.0)


@respx.mock
def test_get_recorded_passes_query_params() -> None:
    """get_recorded sends the right query params to the API."""
    route = respx.get(f"{BASE}/streams/{WEB_ID}/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        streams.get_recorded(WEB_ID, start_time="-2h", end_time="*", max_count=500)

    assert route.called
    request = route.calls.last.request
    assert b"startTime=-2h" in request.url.query
    assert b"maxCount=500" in request.url.query


@respx.mock
def test_get_recorded_server_error_raises() -> None:
    """get_recorded raises on 500."""
    respx.get(f"{BASE}/streams/{WEB_ID}/recorded").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        with pytest.raises(httpx.HTTPStatusError):
            streams.get_recorded(WEB_ID)


# ===========================================================================
# Sync — get_interpolated
# ===========================================================================


@respx.mock
def test_get_interpolated_happy_path() -> None:
    """get_interpolated returns a StreamValues collection."""
    respx.get(f"{BASE}/streams/{WEB_ID}/interpolated").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        vals = streams.get_interpolated(WEB_ID, start_time="-1h", end_time="*", interval="5m")

    assert isinstance(vals, StreamValues)
    assert len(vals) == 2


@respx.mock
def test_get_interpolated_passes_interval_param() -> None:
    """get_interpolated forwards the interval parameter."""
    route = respx.get(f"{BASE}/streams/{WEB_ID}/interpolated").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        streams.get_interpolated(WEB_ID, interval="15m")

    assert b"interval=15m" in route.calls.last.request.url.query


# ===========================================================================
# Sync — update_value
# ===========================================================================


@respx.mock
def test_update_value_happy_path() -> None:
    """update_value posts the value and returns None on 204."""
    route = respx.post(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(204)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        result = streams.update_value(WEB_ID, 99.9)

    assert result is None
    assert route.called


@respx.mock
def test_update_value_with_timestamp() -> None:
    """update_value includes Timestamp in the request body when provided."""
    route = respx.post(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(204)
    )
    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        streams.update_value(WEB_ID, 42.0, timestamp=ts)

    import json

    body = json.loads(route.calls.last.request.content)
    assert body["Value"] == pytest.approx(42.0)
    assert "2024-06-01" in body["Timestamp"]


@respx.mock
def test_update_value_with_string_timestamp() -> None:
    """update_value accepts PI time strings for timestamp."""
    route = respx.post(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(204)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        streams.update_value(WEB_ID, 1.5, timestamp="2024-06-01T00:00:00Z")

    import json

    body = json.loads(route.calls.last.request.content)
    assert body["Timestamp"] == "2024-06-01T00:00:00Z"


@respx.mock
def test_update_value_auth_error_raises() -> None:
    """update_value raises on 401."""
    respx.post(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        with pytest.raises(httpx.HTTPStatusError):
            streams.update_value(WEB_ID, 0.0)


# ===========================================================================
# Sync — update_values
# ===========================================================================


@respx.mock
def test_update_values_happy_path() -> None:
    """update_values posts a list of values and returns None."""
    route = respx.post(f"{BASE}/streams/{WEB_ID}/recorded").mock(
        return_value=httpx.Response(202)
    )
    payload = [
        {"Value": 1.0, "Timestamp": "2024-06-01T10:00:00Z"},
        {"Value": 2.0, "Timestamp": "2024-06-01T11:00:00Z"},
    ]

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        result = streams.update_values(WEB_ID, payload)

    assert result is None
    assert route.called


@respx.mock
def test_update_values_server_error_raises() -> None:
    """update_values raises on 500."""
    respx.post(f"{BASE}/streams/{WEB_ID}/recorded").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        with pytest.raises(httpx.HTTPStatusError):
            streams.update_values(WEB_ID, [{"Value": 1.0}])


# ===========================================================================
# Async — get_value
# ===========================================================================


@respx.mock
async def test_async_get_value_happy_path() -> None:
    """Async get_value returns a StreamValue on 200."""
    respx.get(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(200, json=VALUE_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        val = await streams.get_value(WEB_ID)

    assert val.value == pytest.approx(3.14)
    assert val.good is True


@respx.mock
async def test_async_get_value_404_raises() -> None:
    """Async get_value raises on 404."""
    respx.get(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        with pytest.raises(httpx.HTTPStatusError):
            await streams.get_value(WEB_ID)


# ===========================================================================
# Async — get_recorded
# ===========================================================================


@respx.mock
async def test_async_get_recorded_happy_path() -> None:
    """Async get_recorded returns a StreamValues collection."""
    respx.get(f"{BASE}/streams/{WEB_ID}/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        vals = await streams.get_recorded(WEB_ID)

    assert len(vals) == 2


# ===========================================================================
# Async — get_interpolated
# ===========================================================================


@respx.mock
async def test_async_get_interpolated_happy_path() -> None:
    """Async get_interpolated returns a StreamValues collection."""
    respx.get(f"{BASE}/streams/{WEB_ID}/interpolated").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        vals = await streams.get_interpolated(WEB_ID)

    assert isinstance(vals, StreamValues)
    assert len(vals) == 2


# ===========================================================================
# Async — update_value
# ===========================================================================


@respx.mock
async def test_async_update_value_happy_path() -> None:
    """Async update_value posts a value and returns None."""
    route = respx.post(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(204)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        result = await streams.update_value(WEB_ID, 55.5)

    assert result is None
    assert route.called


# ===========================================================================
# Async — update_values
# ===========================================================================


@respx.mock
async def test_async_update_values_happy_path() -> None:
    """Async update_values posts a list of values and returns None."""
    route = respx.post(f"{BASE}/streams/{WEB_ID}/recorded").mock(
        return_value=httpx.Response(202)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        result = await streams.update_values(WEB_ID, [{"Value": 9.9}])

    assert result is None
    assert route.called
