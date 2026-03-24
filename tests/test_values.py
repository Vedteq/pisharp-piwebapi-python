"""Tests for Streams/Values resource — sync and async."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import AuthenticationError, NotFoundError, ServerError
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
    """get_value raises NotFoundError on 404."""
    respx.get(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(404, json={"Message": "Stream not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        with pytest.raises(NotFoundError) as exc_info:
            streams.get_value(WEB_ID)

    assert exc_info.value.status_code == 404
    assert "Stream not found" in str(exc_info.value)


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
    """get_recorded raises ServerError on 500."""
    respx.get(f"{BASE}/streams/{WEB_ID}/recorded").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        with pytest.raises(ServerError) as exc_info:
            streams.get_recorded(WEB_ID)

    assert exc_info.value.status_code == 500


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

    body = json.loads(route.calls.last.request.content)
    assert body["Timestamp"] == "2024-06-01T00:00:00Z"


@respx.mock
def test_update_value_auth_error_raises() -> None:
    """update_value raises AuthenticationError on 401."""
    respx.post(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        with pytest.raises(AuthenticationError) as exc_info:
            streams.update_value(WEB_ID, 0.0)

    assert exc_info.value.status_code == 401


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
    """update_values raises ServerError on 500."""
    respx.post(f"{BASE}/streams/{WEB_ID}/recorded").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        with pytest.raises(ServerError):
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
    """Async get_value raises NotFoundError on 404."""
    respx.get(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        with pytest.raises(NotFoundError) as exc_info:
            await streams.get_value(WEB_ID)

    assert exc_info.value.status_code == 404


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


@respx.mock
async def test_async_update_value_server_error_raises() -> None:
    """Async update_value raises ServerError on 500."""
    respx.post(f"{BASE}/streams/{WEB_ID}/value").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        with pytest.raises(ServerError):
            await streams.update_value(WEB_ID, 0.0)


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


# ===========================================================================
# Shared summary payload
# ===========================================================================

SUMMARY_PAYLOAD = {
    "WebId": WEB_ID,
    "Name": "sinusoid",
    "Path": "",
    "Items": [
        {
            "Type": "Minimum",
            "Value": {
                "Timestamp": "2024-06-01T11:15:00Z",
                "Value": 0.5,
                "Good": True,
                "Questionable": False,
                "Substituted": False,
                "Annotated": False,
                "UnitsAbbreviation": "degC",
            },
        },
        {
            "Type": "Maximum",
            "Value": {
                "Timestamp": "2024-06-01T11:45:00Z",
                "Value": 9.8,
                "Good": True,
                "Questionable": False,
                "Substituted": False,
                "Annotated": False,
                "UnitsAbbreviation": "degC",
            },
        },
        {
            "Type": "Mean",
            "Value": {
                "Timestamp": "2024-06-01T11:00:00Z",
                "Value": 5.1,
                "Good": True,
                "Questionable": False,
                "Substituted": False,
                "Annotated": False,
                "UnitsAbbreviation": "degC",
            },
        },
    ],
    "Links": {},
}


# ===========================================================================
# Sync — get_summary
# ===========================================================================


@respx.mock
def test_get_summary_happy_path() -> None:
    """get_summary returns a StreamSummary with the expected items."""
    from pisharp_piwebapi.models import StreamSummary, StreamSummaryValue

    respx.get(f"{BASE}/streams/{WEB_ID}/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        summary = streams.get_summary(WEB_ID)

    assert isinstance(summary, StreamSummary)
    assert summary.web_id == WEB_ID
    assert len(summary.items) == 3
    assert all(isinstance(item, StreamSummaryValue) for item in summary.items)
    types = [item.type for item in summary.items]
    assert "Minimum" in types
    assert "Maximum" in types
    assert "Mean" in types


@respx.mock
def test_get_summary_as_dict() -> None:
    """StreamSummary.as_dict returns a flat {type: raw_value} mapping."""
    respx.get(f"{BASE}/streams/{WEB_ID}/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        summary = streams.get_summary(WEB_ID)

    d = summary.as_dict()
    assert d["Minimum"] == pytest.approx(0.5)
    assert d["Maximum"] == pytest.approx(9.8)
    assert d["Mean"] == pytest.approx(5.1)


@respx.mock
def test_get_summary_passes_query_params() -> None:
    """get_summary forwards all four query parameters to the API."""
    route = respx.get(f"{BASE}/streams/{WEB_ID}/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        streams.get_summary(
            WEB_ID,
            start_time="-8h",
            end_time="*",
            summary_type="Minimum,Maximum",
            calculation_basis="EventWeighted",
        )

    raw_query = route.calls.last.request.url.query.decode()
    assert "startTime=-8h" in raw_query
    assert "summaryType=Minimum" in raw_query
    assert "calculationBasis=EventWeighted" in raw_query


@respx.mock
def test_get_summary_404_raises() -> None:
    """get_summary raises NotFoundError on 404."""
    respx.get(f"{BASE}/streams/{WEB_ID}/summary").mock(
        return_value=httpx.Response(404, json={"Message": "Stream not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        with pytest.raises(NotFoundError) as exc_info:
            streams.get_summary(WEB_ID)

    assert exc_info.value.status_code == 404
    assert "Stream not found" in str(exc_info.value)


@respx.mock
def test_get_summary_server_error_raises() -> None:
    """get_summary raises ServerError on 500."""
    respx.get(f"{BASE}/streams/{WEB_ID}/summary").mock(
        return_value=httpx.Response(500, json={"Message": "Internal error"})
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        with pytest.raises(ServerError) as exc_info:
            streams.get_summary(WEB_ID)

    assert exc_info.value.status_code == 500


# ===========================================================================
# Async — get_summary
# ===========================================================================


@respx.mock
async def test_async_get_summary_happy_path() -> None:
    """Async get_summary returns a StreamSummary with the expected items."""
    from pisharp_piwebapi.models import StreamSummary

    respx.get(f"{BASE}/streams/{WEB_ID}/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        summary = await streams.get_summary(WEB_ID)

    assert isinstance(summary, StreamSummary)
    assert len(summary.items) == 3
    d = summary.as_dict()
    assert d["Maximum"] == pytest.approx(9.8)


@respx.mock
async def test_async_get_summary_404_raises() -> None:
    """Async get_summary raises NotFoundError on 404."""
    respx.get(f"{BASE}/streams/{WEB_ID}/summary").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        with pytest.raises(NotFoundError) as exc_info:
            await streams.get_summary(WEB_ID)

    assert exc_info.value.status_code == 404


@respx.mock
async def test_async_get_summary_passes_query_params() -> None:
    """Async get_summary forwards startTime, endTime, summaryType, and calculationBasis."""
    route = respx.get(f"{BASE}/streams/{WEB_ID}/summary").mock(
        return_value=httpx.Response(200, json=SUMMARY_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        await streams.get_summary(
            WEB_ID,
            start_time="-4h",
            summary_type="Mean",
            calculation_basis="EventWeighted",
        )

    raw_query = route.calls.last.request.url.query.decode()
    assert "startTime=-4h" in raw_query
    assert "summaryType=Mean" in raw_query
    assert "calculationBasis=EventWeighted" in raw_query


# ===========================================================================
# Sync — get_plot
# ===========================================================================

PLOT_PAYLOAD = {
    "WebId": WEB_ID,
    "Name": "sinusoid",
    "Path": "",
    "Items": [
        {"Timestamp": "2024-06-01T11:00:00Z", "Value": 1.0, "Good": True},
        {"Timestamp": "2024-06-01T11:15:00Z", "Value": 9.5, "Good": True},
        {"Timestamp": "2024-06-01T11:30:00Z", "Value": 0.2, "Good": True},
        {"Timestamp": "2024-06-01T11:45:00Z", "Value": 8.8, "Good": True},
        {"Timestamp": "2024-06-01T12:00:00Z", "Value": 5.0, "Good": True},
    ],
    "UnitsAbbreviation": "degC",
    "Links": {},
}


@respx.mock
def test_get_plot_happy_path() -> None:
    """get_plot returns a StreamValues collection with plot-optimized data."""
    respx.get(f"{BASE}/streams/{WEB_ID}/plot").mock(
        return_value=httpx.Response(200, json=PLOT_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        vals = streams.get_plot(WEB_ID, start_time="-1h", end_time="*")

    assert isinstance(vals, StreamValues)
    assert len(vals) == 5


@respx.mock
def test_get_plot_passes_intervals_param() -> None:
    """get_plot forwards the intervals parameter to the API."""
    route = respx.get(f"{BASE}/streams/{WEB_ID}/plot").mock(
        return_value=httpx.Response(200, json=PLOT_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        streams.get_plot(WEB_ID, intervals=48)

    raw_query = route.calls.last.request.url.query.decode()
    assert "intervals=48" in raw_query


@respx.mock
def test_get_plot_404_raises() -> None:
    """get_plot raises NotFoundError on 404."""
    respx.get(f"{BASE}/streams/{WEB_ID}/plot").mock(
        return_value=httpx.Response(404, json={"Message": "Stream not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        streams = _SyncStreams(client)
        with pytest.raises(NotFoundError):
            streams.get_plot(WEB_ID)


# ===========================================================================
# Async — get_plot
# ===========================================================================


@respx.mock
async def test_async_get_plot_happy_path() -> None:
    """Async get_plot returns a StreamValues collection."""
    respx.get(f"{BASE}/streams/{WEB_ID}/plot").mock(
        return_value=httpx.Response(200, json=PLOT_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        vals = await streams.get_plot(WEB_ID, start_time="-8h", intervals=12)

    assert isinstance(vals, StreamValues)
    assert len(vals) == 5


@respx.mock
async def test_async_get_plot_404_raises() -> None:
    """Async get_plot raises NotFoundError on 404."""
    respx.get(f"{BASE}/streams/{WEB_ID}/plot").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        streams = _AsyncStreams(client)
        with pytest.raises(NotFoundError):
            await streams.get_plot(WEB_ID)
