"""Tests for Categories resource (element, analysis, attribute) — sync and async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.categories import (
    AnalysisCategoriesMixin,
    AsyncAnalysisCategoriesMixin,
    AsyncAttributeCategoriesMixin,
    AsyncElementCategoriesMixin,
    AttributeCategoriesMixin,
    ElementCategoriesMixin,
)
from pisharp_piwebapi.exceptions import NotFoundError, ServerError
from pisharp_piwebapi.models import PICategory

BASE = "https://piserver/piwebapi"
EC_WID = "EC0prod001"
AC_WID = "AC0calc001"
ATC_WID = "ATC0temp001"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

CATEGORY_PAYLOAD = {
    "WebId": EC_WID,
    "Id": "guid-ec-001",
    "Name": "Production",
    "Description": "Production equipment",
    "Path": "\\\\AF_SERVER\\DB\\ElementCategories[Production]",
    "Links": {"Self": f"{BASE}/elementcategories/{EC_WID}"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SyncEC(ElementCategoriesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncEC(AsyncElementCategoriesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _SyncAC(AnalysisCategoriesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncAC(AsyncAnalysisCategoriesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _SyncATC(AttributeCategoriesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncATC(AsyncAttributeCategoriesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — ElementCategories
# ===========================================================================


@respx.mock
def test_ec_get_by_web_id_happy_path() -> None:
    """ElementCategories get_by_web_id returns a PICategory."""
    respx.get(f"{BASE}/elementcategories/{EC_WID}").mock(
        return_value=httpx.Response(200, json=CATEGORY_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        ec = _SyncEC(client)
        result = ec.get_by_web_id(EC_WID)
    assert isinstance(result, PICategory)
    assert result.web_id == EC_WID
    assert result.name == "Production"


@respx.mock
def test_ec_get_by_web_id_404_raises() -> None:
    """ElementCategories get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/elementcategories/{EC_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        ec = _SyncEC(client)
        with pytest.raises(NotFoundError):
            ec.get_by_web_id(EC_WID)


@respx.mock
def test_ec_get_by_path_happy_path() -> None:
    """ElementCategories get_by_path returns a PICategory."""
    route = respx.get(f"{BASE}/elementcategories").mock(
        return_value=httpx.Response(200, json=CATEGORY_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        ec = _SyncEC(client)
        result = ec.get_by_path("\\\\AF_SERVER\\DB\\ElementCategories[Production]")
    assert isinstance(result, PICategory)
    assert route.called
    assert b"path=" in route.calls.last.request.url.query


@respx.mock
def test_ec_update_happy_path() -> None:
    """ElementCategories update sends PATCH."""
    route = respx.patch(f"{BASE}/elementcategories/{EC_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        ec = _SyncEC(client)
        ec.update(EC_WID, {"Description": "updated"})
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["Description"] == "updated"


@respx.mock
def test_ec_delete_happy_path() -> None:
    """ElementCategories delete sends DELETE."""
    route = respx.delete(f"{BASE}/elementcategories/{EC_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        ec = _SyncEC(client)
        ec.delete(EC_WID)
    assert route.called


@respx.mock
def test_ec_delete_404_raises() -> None:
    """ElementCategories delete raises NotFoundError on 404."""
    respx.delete(f"{BASE}/elementcategories/{EC_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        ec = _SyncEC(client)
        with pytest.raises(NotFoundError):
            ec.delete(EC_WID)


# ===========================================================================
# Sync — AnalysisCategories (verify different prefix)
# ===========================================================================


@respx.mock
def test_ac_get_by_web_id_happy_path() -> None:
    """AnalysisCategories get_by_web_id hits the correct endpoint."""
    payload = {**CATEGORY_PAYLOAD, "WebId": AC_WID, "Name": "CalcCategory"}
    respx.get(f"{BASE}/analysiscategories/{AC_WID}").mock(
        return_value=httpx.Response(200, json=payload)
    )
    with httpx.Client(base_url=BASE) as client:
        ac = _SyncAC(client)
        result = ac.get_by_web_id(AC_WID)
    assert result.name == "CalcCategory"


@respx.mock
def test_ac_update_happy_path() -> None:
    """AnalysisCategories update sends PATCH to correct endpoint."""
    route = respx.patch(f"{BASE}/analysiscategories/{AC_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        ac = _SyncAC(client)
        ac.update(AC_WID, {"Description": "updated"})
    assert route.called


# ===========================================================================
# Sync — AttributeCategories (verify different prefix)
# ===========================================================================


@respx.mock
def test_atc_get_by_web_id_happy_path() -> None:
    """AttributeCategories get_by_web_id hits the correct endpoint."""
    payload = {**CATEGORY_PAYLOAD, "WebId": ATC_WID, "Name": "TempCat"}
    respx.get(f"{BASE}/attributecategories/{ATC_WID}").mock(
        return_value=httpx.Response(200, json=payload)
    )
    with httpx.Client(base_url=BASE) as client:
        atc = _SyncATC(client)
        result = atc.get_by_web_id(ATC_WID)
    assert result.name == "TempCat"


@respx.mock
def test_atc_delete_happy_path() -> None:
    """AttributeCategories delete sends DELETE to correct endpoint."""
    route = respx.delete(f"{BASE}/attributecategories/{ATC_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        atc = _SyncATC(client)
        atc.delete(ATC_WID)
    assert route.called


# ===========================================================================
# Async — ElementCategories
# ===========================================================================


@respx.mock
async def test_async_ec_get_by_web_id_happy_path() -> None:
    """Async ElementCategories get_by_web_id returns a PICategory."""
    respx.get(f"{BASE}/elementcategories/{EC_WID}").mock(
        return_value=httpx.Response(200, json=CATEGORY_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        ec = _AsyncEC(client)
        result = await ec.get_by_web_id(EC_WID)
    assert isinstance(result, PICategory)
    assert result.web_id == EC_WID


@respx.mock
async def test_async_ec_get_by_web_id_404_raises() -> None:
    """Async ElementCategories get_by_web_id raises NotFoundError."""
    respx.get(f"{BASE}/elementcategories/{EC_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        ec = _AsyncEC(client)
        with pytest.raises(NotFoundError):
            await ec.get_by_web_id(EC_WID)


@respx.mock
async def test_async_ec_get_by_path_happy_path() -> None:
    """Async ElementCategories get_by_path returns a PICategory."""
    respx.get(f"{BASE}/elementcategories").mock(
        return_value=httpx.Response(200, json=CATEGORY_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        ec = _AsyncEC(client)
        result = await ec.get_by_path("\\\\AF\\DB\\ElementCategories[Prod]")
    assert isinstance(result, PICategory)


@respx.mock
async def test_async_ec_update_happy_path() -> None:
    """Async ElementCategories update sends PATCH."""
    route = respx.patch(f"{BASE}/elementcategories/{EC_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        ec = _AsyncEC(client)
        await ec.update(EC_WID, {"Description": "updated"})
    assert route.called


@respx.mock
async def test_async_ec_delete_happy_path() -> None:
    """Async ElementCategories delete sends DELETE."""
    route = respx.delete(f"{BASE}/elementcategories/{EC_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        ec = _AsyncEC(client)
        await ec.delete(EC_WID)
    assert route.called


# ===========================================================================
# Async — AnalysisCategories
# ===========================================================================


@respx.mock
async def test_async_ac_get_by_web_id_happy_path() -> None:
    """Async AnalysisCategories get_by_web_id hits correct endpoint."""
    payload = {**CATEGORY_PAYLOAD, "WebId": AC_WID, "Name": "CalcCat"}
    respx.get(f"{BASE}/analysiscategories/{AC_WID}").mock(
        return_value=httpx.Response(200, json=payload)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        ac = _AsyncAC(client)
        result = await ac.get_by_web_id(AC_WID)
    assert result.name == "CalcCat"


# ===========================================================================
# Async — AttributeCategories
# ===========================================================================


@respx.mock
async def test_async_atc_get_by_web_id_happy_path() -> None:
    """Async AttributeCategories get_by_web_id hits correct endpoint."""
    payload = {**CATEGORY_PAYLOAD, "WebId": ATC_WID, "Name": "TempCat"}
    respx.get(f"{BASE}/attributecategories/{ATC_WID}").mock(
        return_value=httpx.Response(200, json=payload)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        atc = _AsyncATC(client)
        result = await atc.get_by_web_id(ATC_WID)
    assert result.name == "TempCat"


@respx.mock
async def test_async_atc_delete_server_error_raises() -> None:
    """Async AttributeCategories delete raises ServerError on 500."""
    respx.delete(f"{BASE}/attributecategories/{ATC_WID}").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        atc = _AsyncATC(client)
        with pytest.raises(ServerError):
            await atc.delete(ATC_WID)
