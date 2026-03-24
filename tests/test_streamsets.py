"""Tests for StreamSets resource — sync and async."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import AuthenticationError, NotFoundError, ServerError
from pisharp_piwebapi.models import StreamSetItem, StreamValue
from pisharp_piwebapi.streamsets import AsyncStreamSetsMixin, StreamSetsMixin

BASE = "https://piserver/piwebapi"
WEB_ID_A = "F1AbEDFoo001"
WEB_ID_B = "F1AbEDFoo002"
ELEM_WEB_ID = "F1AbEDElem99"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

# PI Web API /streamsets/value returns a plain list (no outer "Items" wrapper)
SNAPSHOT_PAYLOAD = [
    {
        "WebId": WEB_ID_A,
        "Name": "sinusoid",
        "Timestamp": "2024-06-01T12:00:00Z",
        "Value": 1.23,
        "UnitsAbbreviation": "degC",
        "Good": True,
        "Questionable": False,
        "Substituted": False,
        "Annotated": False,
    },
    {
        "WebId": WEB_ID_B,
        "Name": "cdt158",
        "Timestamp": "2024-06-01T12:00:00Z",
        "Value": 4.56,
        "UnitsAbbreviation": "",
        "Good": True,
        "Questionable": False,
        "Substituted": False,
        "Annotated": False,
    },
]

# /streamsets/recorded and /streamsets/interpolated wrap results in {"Items": [...]}
RECORDED_PAYLOAD = {
    "Items": [
        {
            "WebId": WEB_ID_A,
            "Name": "sinusoid",
            "Path": "",
            "Items": [
                {"Timestamp": "2024-06-01T11:00:00Z", "Value": 1.0, "Good": True},
                {"Timestamp": "2024-06-01T12:00:00Z", "Value": 2.0, "Good": True},
            ],
            "UnitsAbbreviation": "degC",
            "Links": {},
        },
        {
            "WebId": WEB_ID_B,
            "Name": "cdt158",
            "Path": "",
            "Items": [
                {"Timestamp": "2024-06-01T11:00:00Z", "Value": 10.0, "Good": True},
            ],
            "UnitsAbbreviation": "",
            "Links": {},
        },
    ]
}

# ---------------------------------------------------------------------------
# Sync / Async helper wrappers
# ---------------------------------------------------------------------------


class _SyncStreamSets(StreamSetsMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncStreamSets(AsyncStreamSetsMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_values (snapshot)
# ===========================================================================


@respx.mock
def test_get_values_happy_path() -> None:
    """get_values returns a StreamValue per WebID on 200."""
    respx.get(f"{BASE}/streamsets/value").mock(
        return_value=httpx.Response(200, json=SNAPSHOT_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        result = ss.get_values([WEB_ID_A, WEB_ID_B])

    assert len(result) == 2
    assert all(isinstance(v, StreamValue) for v in result)
    assert result[0].value == pytest.approx(1.23)
    assert result[1].value == pytest.approx(4.56)


@respx.mock
def test_get_values_sends_multiple_web_id_params() -> None:
    """get_values encodes each WebID as a separate webId= query parameter."""
    route = respx.get(f"{BASE}/streamsets/value").mock(
        return_value=httpx.Response(200, json=SNAPSHOT_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        ss.get_values([WEB_ID_A, WEB_ID_B])

    raw_query = route.calls.last.request.url.query.decode()
    assert f"webId={WEB_ID_A}" in raw_query
    assert f"webId={WEB_ID_B}" in raw_query


@respx.mock
def test_get_values_401_raises() -> None:
    """get_values raises AuthenticationError on 401."""
    respx.get(f"{BASE}/streamsets/value").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        with pytest.raises(AuthenticationError) as exc_info:
            ss.get_values([WEB_ID_A])

    assert exc_info.value.status_code == 401


# ===========================================================================
# Sync — get_recorded_ad_hoc
# ===========================================================================


@respx.mock
def test_get_recorded_ad_hoc_happy_path() -> None:
    """get_recorded_ad_hoc returns a StreamSetItem per WebID."""
    respx.get(f"{BASE}/streamsets/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        result = ss.get_recorded_ad_hoc([WEB_ID_A, WEB_ID_B], start_time="-2h")

    assert len(result) == 2
    assert all(isinstance(item, StreamSetItem) for item in result)
    assert result[0].web_id == WEB_ID_A
    assert len(result[0].items) == 2
    assert result[1].web_id == WEB_ID_B
    assert len(result[1].items) == 1


@respx.mock
def test_get_recorded_ad_hoc_passes_params() -> None:
    """get_recorded_ad_hoc forwards startTime, endTime, and maxCount."""
    route = respx.get(f"{BASE}/streamsets/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        ss.get_recorded_ad_hoc([WEB_ID_A], start_time="-8h", end_time="*", max_count=500)

    raw_query = route.calls.last.request.url.query.decode()
    assert "startTime=-8h" in raw_query
    assert "maxCount=500" in raw_query


@respx.mock
def test_get_recorded_ad_hoc_server_error_raises() -> None:
    """get_recorded_ad_hoc raises ServerError on 500."""
    respx.get(f"{BASE}/streamsets/recorded").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        with pytest.raises(ServerError) as exc_info:
            ss.get_recorded_ad_hoc([WEB_ID_A])

    assert exc_info.value.status_code == 500


# ===========================================================================
# Sync — get_interpolated_ad_hoc
# ===========================================================================


@respx.mock
def test_get_interpolated_ad_hoc_happy_path() -> None:
    """get_interpolated_ad_hoc returns a StreamSetItem per WebID."""
    respx.get(f"{BASE}/streamsets/interpolated").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        result = ss.get_interpolated_ad_hoc([WEB_ID_A, WEB_ID_B], interval="15m")

    assert len(result) == 2
    assert result[0].web_id == WEB_ID_A


@respx.mock
def test_get_interpolated_ad_hoc_passes_interval() -> None:
    """get_interpolated_ad_hoc forwards the interval parameter."""
    route = respx.get(f"{BASE}/streamsets/interpolated").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        ss.get_interpolated_ad_hoc([WEB_ID_A], interval="30m")

    assert b"interval=30m" in route.calls.last.request.url.query


# ===========================================================================
# Sync — get_recorded_by_element
# ===========================================================================


@respx.mock
def test_get_recorded_by_element_happy_path() -> None:
    """get_recorded_by_element reads all attributes of an AF element."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        result = ss.get_recorded_by_element(ELEM_WEB_ID)

    assert len(result) == 2
    assert all(isinstance(item, StreamSetItem) for item in result)


@respx.mock
def test_get_recorded_by_element_passes_params() -> None:
    """get_recorded_by_element forwards startTime, endTime, maxCount, nameFilter."""
    route = respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        ss.get_recorded_by_element(
            ELEM_WEB_ID,
            start_time="-4h",
            max_count=250,
            name_filter="Temp*",
        )

    raw_query = route.calls.last.request.url.query.decode()
    assert "startTime=-4h" in raw_query
    assert "maxCount=250" in raw_query
    assert "nameFilter=Temp" in raw_query


@respx.mock
def test_get_recorded_by_element_404_raises() -> None:
    """get_recorded_by_element raises NotFoundError on 404."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/recorded").mock(
        return_value=httpx.Response(404, json={"Message": "Element not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        with pytest.raises(NotFoundError) as exc_info:
            ss.get_recorded_by_element(ELEM_WEB_ID)

    assert exc_info.value.status_code == 404
    assert "Element not found" in str(exc_info.value)


# ===========================================================================
# Async — get_values
# ===========================================================================


@respx.mock
async def test_async_get_values_happy_path() -> None:
    """Async get_values returns a StreamValue per WebID."""
    respx.get(f"{BASE}/streamsets/value").mock(
        return_value=httpx.Response(200, json=SNAPSHOT_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        result = await ss.get_values([WEB_ID_A, WEB_ID_B])

    assert len(result) == 2
    assert result[0].value == pytest.approx(1.23)


@respx.mock
async def test_async_get_values_401_raises() -> None:
    """Async get_values raises AuthenticationError on 401."""
    respx.get(f"{BASE}/streamsets/value").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        with pytest.raises(AuthenticationError) as exc_info:
            await ss.get_values([WEB_ID_A])

    assert exc_info.value.status_code == 401


# ===========================================================================
# Async — get_recorded_ad_hoc
# ===========================================================================


@respx.mock
async def test_async_get_recorded_ad_hoc_happy_path() -> None:
    """Async get_recorded_ad_hoc returns a StreamSetItem per WebID."""
    respx.get(f"{BASE}/streamsets/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        result = await ss.get_recorded_ad_hoc([WEB_ID_A, WEB_ID_B])

    assert len(result) == 2
    assert result[0].web_id == WEB_ID_A


@respx.mock
async def test_async_get_recorded_ad_hoc_server_error_raises() -> None:
    """Async get_recorded_ad_hoc raises ServerError on 503."""
    respx.get(f"{BASE}/streamsets/recorded").mock(
        return_value=httpx.Response(503, json={"Message": "Unavailable"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        with pytest.raises(ServerError) as exc_info:
            await ss.get_recorded_ad_hoc([WEB_ID_A])

    assert exc_info.value.status_code == 503


# ===========================================================================
# Async — get_interpolated_ad_hoc
# ===========================================================================


@respx.mock
async def test_async_get_interpolated_ad_hoc_happy_path() -> None:
    """Async get_interpolated_ad_hoc returns a StreamSetItem per WebID."""
    respx.get(f"{BASE}/streamsets/interpolated").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        result = await ss.get_interpolated_ad_hoc([WEB_ID_A, WEB_ID_B], interval="5m")

    assert len(result) == 2


# ===========================================================================
# Async — get_recorded_by_element
# ===========================================================================


@respx.mock
async def test_async_get_recorded_by_element_happy_path() -> None:
    """Async get_recorded_by_element reads all attributes of an AF element."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/recorded").mock(
        return_value=httpx.Response(200, json=RECORDED_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        result = await ss.get_recorded_by_element(ELEM_WEB_ID)

    assert len(result) == 2
    assert all(isinstance(item, StreamSetItem) for item in result)


@respx.mock
async def test_async_get_recorded_by_element_404_raises() -> None:
    """Async get_recorded_by_element raises NotFoundError on 404."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/recorded").mock(
        return_value=httpx.Response(404, json={"Message": "Element not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        with pytest.raises(NotFoundError) as exc_info:
            await ss.get_recorded_by_element(ELEM_WEB_ID)

    assert exc_info.value.status_code == 404


# ===========================================================================
# Sync — get_interpolated_by_element
# ===========================================================================

# Reuse RECORDED_PAYLOAD here — interpolated responses use the same shape.
INTERPOLATED_BY_ELEM_PAYLOAD = {
    "Items": [
        {
            "WebId": WEB_ID_A,
            "Name": "Temperature",
            "Path": "",
            "Items": [
                {"Timestamp": "2024-06-01T11:00:00Z", "Value": 72.1, "Good": True},
                {"Timestamp": "2024-06-01T11:10:00Z", "Value": 72.4, "Good": True},
                {"Timestamp": "2024-06-01T11:20:00Z", "Value": 72.8, "Good": True},
            ],
            "UnitsAbbreviation": "degF",
            "Links": {},
        },
        {
            "WebId": WEB_ID_B,
            "Name": "Pressure",
            "Path": "",
            "Items": [
                {"Timestamp": "2024-06-01T11:00:00Z", "Value": 14.7, "Good": True},
                {"Timestamp": "2024-06-01T11:10:00Z", "Value": 14.8, "Good": True},
            ],
            "UnitsAbbreviation": "psi",
            "Links": {},
        },
    ]
}


@respx.mock
def test_get_interpolated_by_element_happy_path() -> None:
    """get_interpolated_by_element returns a StreamSetItem per attribute."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/interpolated").mock(
        return_value=httpx.Response(200, json=INTERPOLATED_BY_ELEM_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        result = ss.get_interpolated_by_element(ELEM_WEB_ID)

    assert len(result) == 2
    assert all(isinstance(item, StreamSetItem) for item in result)
    assert result[0].web_id == WEB_ID_A
    assert len(result[0].items) == 3
    assert result[1].web_id == WEB_ID_B
    assert len(result[1].items) == 2


@respx.mock
def test_get_interpolated_by_element_passes_params() -> None:
    """get_interpolated_by_element forwards startTime, endTime, interval, and nameFilter."""
    route = respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/interpolated").mock(
        return_value=httpx.Response(200, json=INTERPOLATED_BY_ELEM_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        ss.get_interpolated_by_element(
            ELEM_WEB_ID,
            start_time="-4h",
            end_time="*",
            interval="5m",
            name_filter="Temp*",
        )

    raw_query = route.calls.last.request.url.query.decode()
    assert "startTime=-4h" in raw_query
    assert "interval=5m" in raw_query
    assert "nameFilter=Temp" in raw_query


@respx.mock
def test_get_interpolated_by_element_404_raises() -> None:
    """get_interpolated_by_element raises NotFoundError on 404."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/interpolated").mock(
        return_value=httpx.Response(404, json={"Message": "Element not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        with pytest.raises(NotFoundError) as exc_info:
            ss.get_interpolated_by_element(ELEM_WEB_ID)

    assert exc_info.value.status_code == 404
    assert "Element not found" in str(exc_info.value)


@respx.mock
def test_get_interpolated_by_element_server_error_raises() -> None:
    """get_interpolated_by_element raises ServerError on 500."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/interpolated").mock(
        return_value=httpx.Response(500, json={"Message": "Internal error"})
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        with pytest.raises(ServerError) as exc_info:
            ss.get_interpolated_by_element(ELEM_WEB_ID)

    assert exc_info.value.status_code == 500


# ===========================================================================
# Async — get_interpolated_by_element
# ===========================================================================


@respx.mock
async def test_async_get_interpolated_by_element_happy_path() -> None:
    """Async get_interpolated_by_element returns a StreamSetItem per attribute."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/interpolated").mock(
        return_value=httpx.Response(200, json=INTERPOLATED_BY_ELEM_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        result = await ss.get_interpolated_by_element(ELEM_WEB_ID)

    assert len(result) == 2
    assert all(isinstance(item, StreamSetItem) for item in result)
    assert result[0].web_id == WEB_ID_A
    assert result[1].web_id == WEB_ID_B


@respx.mock
async def test_async_get_interpolated_by_element_passes_params() -> None:
    """Async get_interpolated_by_element forwards all query parameters."""
    route = respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/interpolated").mock(
        return_value=httpx.Response(200, json=INTERPOLATED_BY_ELEM_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        await ss.get_interpolated_by_element(
            ELEM_WEB_ID,
            start_time="-2h",
            interval="15m",
            name_filter="Press*",
        )

    raw_query = route.calls.last.request.url.query.decode()
    assert "startTime=-2h" in raw_query
    assert "interval=15m" in raw_query
    assert "nameFilter=Press" in raw_query


@respx.mock
async def test_async_get_interpolated_by_element_404_raises() -> None:
    """Async get_interpolated_by_element raises NotFoundError on 404."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/interpolated").mock(
        return_value=httpx.Response(404, json={"Message": "Element not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        with pytest.raises(NotFoundError) as exc_info:
            await ss.get_interpolated_by_element(ELEM_WEB_ID)

    assert exc_info.value.status_code == 404


@respx.mock
async def test_async_get_interpolated_by_element_server_error_raises() -> None:
    """Async get_interpolated_by_element raises ServerError on 503."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/interpolated").mock(
        return_value=httpx.Response(503, json={"Message": "Service unavailable"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        with pytest.raises(ServerError) as exc_info:
            await ss.get_interpolated_by_element(ELEM_WEB_ID)

    assert exc_info.value.status_code == 503


# ===========================================================================
# Sync — get_values_by_element (snapshot)
# ===========================================================================

# Snapshot-by-element payload: PI Web API wraps in {"Items": [...]}
SNAPSHOT_BY_ELEM_PAYLOAD = {
    "Items": [
        {
            "WebId": WEB_ID_A,
            "Name": "Temperature",
            "Path": "",
            "Items": [
                {"Timestamp": "2024-06-01T12:00:00Z", "Value": 72.1, "Good": True},
            ],
            "UnitsAbbreviation": "degF",
            "Links": {},
        },
        {
            "WebId": WEB_ID_B,
            "Name": "Pressure",
            "Path": "",
            "Items": [
                {"Timestamp": "2024-06-01T12:00:00Z", "Value": 14.7, "Good": True},
            ],
            "UnitsAbbreviation": "psi",
            "Links": {},
        },
    ]
}


@respx.mock
def test_get_values_by_element_happy_path() -> None:
    """get_values_by_element returns a StreamSetItem per attribute."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/value").mock(
        return_value=httpx.Response(200, json=SNAPSHOT_BY_ELEM_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        result = ss.get_values_by_element(ELEM_WEB_ID)

    assert len(result) == 2
    assert all(isinstance(item, StreamSetItem) for item in result)
    assert result[0].web_id == WEB_ID_A
    assert result[0].name == "Temperature"
    assert len(result[0].items) == 1
    assert result[0].items[0].value == pytest.approx(72.1)


@respx.mock
def test_get_values_by_element_passes_name_filter() -> None:
    """get_values_by_element forwards the nameFilter query parameter."""
    route = respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/value").mock(
        return_value=httpx.Response(200, json=SNAPSHOT_BY_ELEM_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        ss.get_values_by_element(ELEM_WEB_ID, name_filter="Temp*")

    raw_query = route.calls.last.request.url.query.decode()
    assert "nameFilter=Temp" in raw_query


@respx.mock
def test_get_values_by_element_404_raises() -> None:
    """get_values_by_element raises NotFoundError on 404."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/value").mock(
        return_value=httpx.Response(404, json={"Message": "Element not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        ss = _SyncStreamSets(client)
        with pytest.raises(NotFoundError) as exc_info:
            ss.get_values_by_element(ELEM_WEB_ID)

    assert exc_info.value.status_code == 404
    assert "Element not found" in str(exc_info.value)


# ===========================================================================
# Async — get_values_by_element (snapshot)
# ===========================================================================


@respx.mock
async def test_async_get_values_by_element_happy_path() -> None:
    """Async get_values_by_element returns a StreamSetItem per attribute."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/value").mock(
        return_value=httpx.Response(200, json=SNAPSHOT_BY_ELEM_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        result = await ss.get_values_by_element(ELEM_WEB_ID)

    assert len(result) == 2
    assert all(isinstance(item, StreamSetItem) for item in result)
    assert result[1].name == "Pressure"


@respx.mock
async def test_async_get_values_by_element_404_raises() -> None:
    """Async get_values_by_element raises NotFoundError on 404."""
    respx.get(f"{BASE}/streamsets/{ELEM_WEB_ID}/value").mock(
        return_value=httpx.Response(404, json={"Message": "Element not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        ss = _AsyncStreamSets(client)
        with pytest.raises(NotFoundError) as exc_info:
            await ss.get_values_by_element(ELEM_WEB_ID)

    assert exc_info.value.status_code == 404
