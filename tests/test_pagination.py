"""Tests for pagination helpers — sync and async."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import ServerError
from pisharp_piwebapi.pagination import AsyncPaginationMixin, PaginationMixin

BASE = "https://piserver/piwebapi"

PAGE1 = {
    "Items": [{"WebId": "A", "Name": "tag1"}, {"WebId": "B", "Name": "tag2"}],
    "Links": {"Next": f"{BASE}/points/search?startIndex=2&maxCount=2"},
}

PAGE2 = {
    "Items": [{"WebId": "C", "Name": "tag3"}],
    "Links": {},
}

SINGLE_PAGE = {
    "Items": [{"WebId": "A", "Name": "tag1"}],
    "Links": {},
}


class _SyncPaginator(PaginationMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncPaginator(AsyncPaginationMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync
# ===========================================================================


@respx.mock
def test_get_all_pages_single_page() -> None:
    """get_all_pages returns all items when there is only one page."""
    respx.get(f"{BASE}/points/search").mock(return_value=httpx.Response(200, json=SINGLE_PAGE))

    with httpx.Client(base_url=BASE) as client:
        pager = _SyncPaginator(client)
        items = pager.get_all_pages("/points/search")

    assert len(items) == 1
    assert items[0]["Name"] == "tag1"


@respx.mock
def test_get_all_pages_follows_next_link() -> None:
    """get_all_pages follows the Links.Next URL across multiple pages."""
    respx.get(f"{BASE}/points/search").mock(
        side_effect=[
            httpx.Response(200, json=PAGE1),
            httpx.Response(200, json=PAGE2),
        ]
    )

    with httpx.Client(base_url=BASE) as client:
        pager = _SyncPaginator(client)
        items = pager.get_all_pages("/points/search")

    assert len(items) == 3
    assert items[0]["Name"] == "tag1"
    assert items[2]["Name"] == "tag3"


@respx.mock
def test_get_all_pages_respects_max_pages() -> None:
    """get_all_pages stops after max_pages even if more pages exist."""
    respx.get(f"{BASE}/points/search").mock(return_value=httpx.Response(200, json=PAGE1))

    with httpx.Client(base_url=BASE) as client:
        pager = _SyncPaginator(client)
        # max_pages=1 means we stop after the first page regardless of Next link
        items = pager.get_all_pages("/points/search", max_pages=1)

    assert len(items) == 2  # Only PAGE1 items


@respx.mock
def test_get_all_pages_passes_initial_params() -> None:
    """get_all_pages sends query params on the first request only."""
    route = respx.get(f"{BASE}/points/search").mock(
        return_value=httpx.Response(200, json=SINGLE_PAGE)
    )

    with httpx.Client(base_url=BASE) as client:
        pager = _SyncPaginator(client)
        pager.get_all_pages("/points/search", params={"q": "sinu*", "maxCount": "10"})

    assert route.called
    request = route.calls.last.request
    assert b"q=sinu" in request.url.query


@respx.mock
def test_get_all_pages_server_error_raises() -> None:
    """get_all_pages raises ServerError on a 500 response."""
    respx.get(f"{BASE}/points/search").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )

    with httpx.Client(base_url=BASE) as client:
        pager = _SyncPaginator(client)
        with pytest.raises(ServerError) as exc_info:
            pager.get_all_pages("/points/search")

    assert exc_info.value.status_code == 500


# ===========================================================================
# Async
# ===========================================================================


@respx.mock
async def test_async_get_all_pages_single_page() -> None:
    """Async get_all_pages returns all items for a single page."""
    respx.get(f"{BASE}/points/search").mock(return_value=httpx.Response(200, json=SINGLE_PAGE))

    async with httpx.AsyncClient(base_url=BASE) as client:
        pager = _AsyncPaginator(client)
        items = await pager.get_all_pages("/points/search")

    assert len(items) == 1
    assert items[0]["Name"] == "tag1"


@respx.mock
async def test_async_get_all_pages_follows_next_link() -> None:
    """Async get_all_pages follows the Links.Next URL across multiple pages."""
    respx.get(f"{BASE}/points/search").mock(
        side_effect=[
            httpx.Response(200, json=PAGE1),
            httpx.Response(200, json=PAGE2),
        ]
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pager = _AsyncPaginator(client)
        items = await pager.get_all_pages("/points/search")

    assert len(items) == 3


@respx.mock
async def test_async_get_all_pages_server_error_raises() -> None:
    """Async get_all_pages raises ServerError on a 503 response."""
    respx.get(f"{BASE}/points/search").mock(
        return_value=httpx.Response(503, json={"Message": "Unavailable"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pager = _AsyncPaginator(client)
        with pytest.raises(ServerError) as exc_info:
            await pager.get_all_pages("/points/search")

    assert exc_info.value.status_code == 503
