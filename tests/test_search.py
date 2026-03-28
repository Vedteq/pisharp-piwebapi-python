"""Tests for the indexed AF Search resource."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import PIWebAPIError
from pisharp_piwebapi.search import AsyncSearchMixin, SearchMixin, SearchResult

BASE = "https://pi.example.com/piwebapi"
DB_WEB_ID = "RDAbEDFDatabase"


class _SyncSearch(SearchMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncSearch(AsyncSearchMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


SEARCH_RESPONSE = {
    "Items": [
        {
            "WebId": "E0AbEDFPump001",
            "Name": "Pump-001",
            "Path": "\\\\AF_SERVER\\DB\\Pump-001",
            "ItemType": "Element",
            "Score": 9.5,
            "Links": {},
        },
        {
            "WebId": "E0AbEDFPump002",
            "Name": "Pump-002",
            "Path": "\\\\AF_SERVER\\DB\\Pump-002",
            "ItemType": "Element",
            "Score": 8.2,
            "Links": {},
        },
    ],
}

EMPTY_RESPONSE: dict[str, list[object]] = {"Items": []}


# --- Sync tests ---


@respx.mock
def test_query_happy_path() -> None:
    """query returns SearchResult objects from /search/query."""
    respx.get(f"{BASE}/search/query").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        s = _SyncSearch(client)
        results = s.query("name:Pump*")

    assert len(results) == 2
    assert isinstance(results[0], SearchResult)
    assert results[0].name == "Pump-001"
    assert results[0].web_id == "E0AbEDFPump001"
    assert results[0].item_type == "Element"
    assert results[0].score == 9.5
    assert results[0].path == "\\\\AF_SERVER\\DB\\Pump-001"


@respx.mock
def test_query_forwards_params() -> None:
    """query forwards scope, fields, max_count, and start_index."""
    route = respx.get(f"{BASE}/search/query").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        s = _SyncSearch(client)
        s.query(
            "name:Pump*",
            scope=DB_WEB_ID,
            fields="Name,WebId",
            max_count=50,
            start_index=10,
        )

    url = str(route.calls.last.request.url)
    assert "q=name" in url
    assert f"scope={DB_WEB_ID}" in url
    assert "count=50" in url
    assert "start=10" in url


@respx.mock
def test_query_omits_optional_params() -> None:
    """scope and fields are not sent when None."""
    route = respx.get(f"{BASE}/search/query").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        s = _SyncSearch(client)
        s.query("Pump*")

    url = str(route.calls.last.request.url)
    assert "scope" not in url
    assert "fields" not in url


@respx.mock
def test_query_empty_results() -> None:
    """query returns empty list when no matches."""
    respx.get(f"{BASE}/search/query").mock(
        return_value=httpx.Response(200, json=EMPTY_RESPONSE)
    )
    with httpx.Client(base_url=BASE) as client:
        s = _SyncSearch(client)
        results = s.query("nonexistent*")

    assert results == []


@respx.mock
def test_query_error_raises() -> None:
    """query raises PIWebAPIError on server error."""
    respx.get(f"{BASE}/search/query").mock(
        return_value=httpx.Response(
            500, json={"Message": "Search index unavailable"}
        )
    )
    with httpx.Client(base_url=BASE) as client:
        s = _SyncSearch(client)
        with pytest.raises(PIWebAPIError, match="Search index"):
            s.query("Pump*")


@respx.mock
def test_query_auth_error() -> None:
    """query raises on 401."""
    respx.get(f"{BASE}/search/query").mock(
        return_value=httpx.Response(
            401, json={"Message": "Unauthorized"}
        )
    )
    with httpx.Client(base_url=BASE) as client:
        s = _SyncSearch(client)
        with pytest.raises(PIWebAPIError):
            s.query("Pump*")


def test_search_result_repr() -> None:
    """SearchResult __repr__ is readable."""
    sr = SearchResult({
        "WebId": "W123",
        "Name": "Test",
        "ItemType": "Element",
    })
    r = repr(sr)
    assert "Test" in r
    assert "Element" in r
    assert "W123" in r


def test_search_result_defaults() -> None:
    """SearchResult handles missing fields gracefully."""
    sr = SearchResult({})
    assert sr.web_id == ""
    assert sr.name == ""
    assert sr.path == ""
    assert sr.item_type == ""
    assert sr.score == 0.0


# --- Async tests ---


@respx.mock
async def test_async_query_happy_path() -> None:
    """Async query returns SearchResult objects."""
    respx.get(f"{BASE}/search/query").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        s = _AsyncSearch(client)
        results = await s.query("name:Pump*")

    assert len(results) == 2
    assert results[0].name == "Pump-001"


@respx.mock
async def test_async_query_forwards_params() -> None:
    """Async query forwards all parameters."""
    route = respx.get(f"{BASE}/search/query").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        s = _AsyncSearch(client)
        await s.query(
            "name:Pump*",
            scope=DB_WEB_ID,
            max_count=25,
        )

    url = str(route.calls.last.request.url)
    assert f"scope={DB_WEB_ID}" in url
    assert "count=25" in url


@respx.mock
async def test_async_query_empty_results() -> None:
    """Async query returns empty list when no matches."""
    respx.get(f"{BASE}/search/query").mock(
        return_value=httpx.Response(200, json=EMPTY_RESPONSE)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        s = _AsyncSearch(client)
        results = await s.query("nonexistent*")

    assert results == []


@respx.mock
async def test_async_query_error_raises() -> None:
    """Async query raises on error."""
    respx.get(f"{BASE}/search/query").mock(
        return_value=httpx.Response(
            500, json={"Message": "Indexer down"}
        )
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        s = _AsyncSearch(client)
        with pytest.raises(PIWebAPIError, match="Indexer down"):
            await s.query("Pump*")
