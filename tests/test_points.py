"""Tests for Points resource — sync and async."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import NotFoundError
from pisharp_piwebapi.models import PIPoint
from pisharp_piwebapi.points import AsyncPointsMixin, PointsMixin

BASE = "https://piserver/piwebapi"

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

POINT_PAYLOAD = {
    "WebId": "P0ABC123",
    "Id": 42,
    "Name": "sinusoid",
    "Path": "\\\\SERVER\\sinusoid",
    "Descriptor": "12 Hour Sinusoid",
    "PointClass": "classic",
    "PointType": "Float32",
    "EngineeringUnits": "degC",
    "Future": False,
    "Links": {"Self": f"{BASE}/points/P0ABC123"},
}

SEARCH_PAYLOAD = {
    "Items": [POINT_PAYLOAD],
    "Links": {},
}


# ---------------------------------------------------------------------------
# Sync helpers
# ---------------------------------------------------------------------------


class _SyncPoints(PointsMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------


class _AsyncPoints(AsyncPointsMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_by_path
# ===========================================================================


@respx.mock
def test_get_by_path_happy_path() -> None:
    """get_by_path returns a populated PIPoint on 200."""
    respx.get(f"{BASE}/points").mock(return_value=httpx.Response(200, json=POINT_PAYLOAD))

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        point = pts.get_by_path(r"\\SERVER\sinusoid")

    assert isinstance(point, PIPoint)
    assert point.web_id == "P0ABC123"
    assert point.name == "sinusoid"
    assert point.point_type == "Float32"
    assert point.engineering_units == "degC"


@respx.mock
def test_get_by_path_not_found_raises() -> None:
    """get_by_path raises NotFoundError on 404."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(404, json={"Message": "Point not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        # Use a raw call so the event hook fires — but PointsMixin calls
        # raise_for_status() directly, so we expect httpx.HTTPStatusError here.
        with pytest.raises(httpx.HTTPStatusError):
            pts.get_by_path(r"\\SERVER\missing")


# ===========================================================================
# Sync — get_by_web_id
# ===========================================================================


@respx.mock
def test_get_by_web_id_happy_path() -> None:
    """get_by_web_id returns a populated PIPoint on 200."""
    respx.get(f"{BASE}/points/P0ABC123").mock(
        return_value=httpx.Response(200, json=POINT_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        point = pts.get_by_web_id("P0ABC123")

    assert point.web_id == "P0ABC123"


@respx.mock
def test_get_by_web_id_server_error_raises() -> None:
    """get_by_web_id raises on 500."""
    respx.get(f"{BASE}/points/BAD").mock(
        return_value=httpx.Response(500, json={"Message": "Internal error"})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        with pytest.raises(httpx.HTTPStatusError):
            pts.get_by_web_id("BAD")


# ===========================================================================
# Sync — search
# ===========================================================================


@respx.mock
def test_search_returns_list() -> None:
    """search returns a list of PIPoint objects."""
    respx.get(f"{BASE}/points/search").mock(
        return_value=httpx.Response(200, json=SEARCH_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        results = pts.search("sinu*")

    assert len(results) == 1
    assert results[0].name == "sinusoid"


@respx.mock
def test_search_plain_list_response() -> None:
    """search handles a bare list response (no Items wrapper)."""
    respx.get(f"{BASE}/points/search").mock(
        return_value=httpx.Response(200, json=[POINT_PAYLOAD])
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        results = pts.search("sinu*")

    assert len(results) == 1


@respx.mock
def test_search_empty_result() -> None:
    """search returns an empty list when no points match."""
    respx.get(f"{BASE}/points/search").mock(
        return_value=httpx.Response(200, json={"Items": [], "Links": {}})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        results = pts.search("nomatch*")

    assert results == []


# ===========================================================================
# Async — get_by_path
# ===========================================================================


@respx.mock
async def test_async_get_by_path_happy_path() -> None:
    """Async get_by_path returns a populated PIPoint on 200."""
    respx.get(f"{BASE}/points").mock(return_value=httpx.Response(200, json=POINT_PAYLOAD))

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        point = await pts.get_by_path(r"\\SERVER\sinusoid")

    assert point.web_id == "P0ABC123"
    assert point.name == "sinusoid"


@respx.mock
async def test_async_get_by_path_not_found_raises() -> None:
    """Async get_by_path raises on 404."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        with pytest.raises(httpx.HTTPStatusError):
            await pts.get_by_path(r"\\SERVER\missing")


# ===========================================================================
# Async — get_by_web_id
# ===========================================================================


@respx.mock
async def test_async_get_by_web_id_happy_path() -> None:
    """Async get_by_web_id returns a populated PIPoint on 200."""
    respx.get(f"{BASE}/points/P0ABC123").mock(
        return_value=httpx.Response(200, json=POINT_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        point = await pts.get_by_web_id("P0ABC123")

    assert point.web_id == "P0ABC123"


# ===========================================================================
# Async — search
# ===========================================================================


@respx.mock
async def test_async_search_returns_list() -> None:
    """Async search returns a list of PIPoint objects."""
    respx.get(f"{BASE}/points/search").mock(
        return_value=httpx.Response(200, json=SEARCH_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        results = await pts.search("sinu*")

    assert len(results) == 1
    assert results[0].name == "sinusoid"
