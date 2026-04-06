"""Tests for UnitClasses resource — sync and async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import NotFoundError, ServerError
from pisharp_piwebapi.models import PIUnit, PIUnitClass
from pisharp_piwebapi.unitclasses import AsyncUnitClassesMixin, UnitClassesMixin

BASE = "https://piserver/piwebapi"
UC_WID = "UC0temperature001"
UNIT_WID = "UN0degF001"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

UC_PAYLOAD = {
    "WebId": UC_WID,
    "Id": "guid-uc-001",
    "Name": "Temperature",
    "Description": "Temperature units",
    "Path": "\\\\SERVER\\UnitClasses[Temperature]",
    "CanonicalUnitName": "kelvin",
    "CanonicalUnitAbbreviation": "K",
    "Links": {"Self": f"{BASE}/unitclasses/{UC_WID}"},
}

UNIT_PAYLOAD = {
    "WebId": UNIT_WID,
    "Id": "guid-un-001",
    "Name": "degree Fahrenheit",
    "Abbreviation": "degF",
    "Description": "Fahrenheit scale",
    "Path": "\\\\SERVER\\UnitClasses[Temperature]\\degF",
    "Factor": 0.5556,
    "Offset": 255.3722,
    "ReferenceFactor": 0.0,
    "ReferenceOffset": 0.0,
    "ReferenceUnitAbbreviation": "",
    "Links": {},
}

UNITS_LIST_PAYLOAD = {
    "Items": [
        UNIT_PAYLOAD,
        {
            "WebId": "UN0degC001",
            "Id": "guid-un-002",
            "Name": "degree Celsius",
            "Abbreviation": "degC",
            "Description": "",
            "Path": "",
            "Factor": 1.0,
            "Offset": 273.15,
            "ReferenceFactor": 0.0,
            "ReferenceOffset": 0.0,
            "ReferenceUnitAbbreviation": "",
            "Links": {},
        },
    ]
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SyncUC(UnitClassesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncUC(AsyncUnitClassesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_by_web_id
# ===========================================================================


@respx.mock
def test_get_by_web_id_happy_path() -> None:
    """get_by_web_id returns a PIUnitClass."""
    respx.get(f"{BASE}/unitclasses/{UC_WID}").mock(
        return_value=httpx.Response(200, json=UC_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        result = uc.get_by_web_id(UC_WID)
    assert isinstance(result, PIUnitClass)
    assert result.web_id == UC_WID
    assert result.name == "Temperature"
    assert result.canonical_unit_abbreviation == "K"


@respx.mock
def test_get_by_web_id_404_raises() -> None:
    """get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/unitclasses/{UC_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        with pytest.raises(NotFoundError):
            uc.get_by_web_id(UC_WID)


# ===========================================================================
# Sync — get_by_path
# ===========================================================================


@respx.mock
def test_get_by_path_happy_path() -> None:
    """get_by_path returns a PIUnitClass."""
    route = respx.get(f"{BASE}/unitclasses").mock(
        return_value=httpx.Response(200, json=UC_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        result = uc.get_by_path("\\\\SERVER\\UnitClasses[Temperature]")
    assert isinstance(result, PIUnitClass)
    assert result.name == "Temperature"
    assert route.called
    assert b"path=" in route.calls.last.request.url.query


# ===========================================================================
# Sync — get_units
# ===========================================================================


@respx.mock
def test_get_units_happy_path() -> None:
    """get_units returns a list of PIUnit."""
    respx.get(f"{BASE}/unitclasses/{UC_WID}/units").mock(
        return_value=httpx.Response(200, json=UNITS_LIST_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        units = uc.get_units(UC_WID)
    assert len(units) == 2
    assert all(isinstance(u, PIUnit) for u in units)
    assert units[0].abbreviation == "degF"
    assert units[1].abbreviation == "degC"


@respx.mock
def test_get_units_404_raises() -> None:
    """get_units raises NotFoundError on 404."""
    respx.get(f"{BASE}/unitclasses/{UC_WID}/units").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        with pytest.raises(NotFoundError):
            uc.get_units(UC_WID)


# ===========================================================================
# Sync — get_canonical_unit
# ===========================================================================


@respx.mock
def test_get_canonical_unit_happy_path() -> None:
    """get_canonical_unit returns a PIUnit."""
    canonical = {
        "WebId": "UN0K001",
        "Id": "guid-un-k",
        "Name": "kelvin",
        "Abbreviation": "K",
        "Factor": 1.0,
        "Offset": 0.0,
        "Links": {},
    }
    respx.get(f"{BASE}/unitclasses/{UC_WID}/canonicalunit").mock(
        return_value=httpx.Response(200, json=canonical)
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        result = uc.get_canonical_unit(UC_WID)
    assert isinstance(result, PIUnit)
    assert result.abbreviation == "K"
    assert result.factor == 1.0


# ===========================================================================
# Sync — create_unit
# ===========================================================================


@respx.mock
def test_create_unit_happy_path() -> None:
    """create_unit sends the correct POST body."""
    route = respx.post(f"{BASE}/unitclasses/{UC_WID}/units").mock(
        return_value=httpx.Response(201)
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        uc.create_unit(
            UC_WID,
            name="degree Rankine",
            abbreviation="degR",
            factor=0.5556,
            offset=0.0,
            description="Rankine scale",
        )
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["Name"] == "degree Rankine"
    assert body["Abbreviation"] == "degR"
    assert body["Factor"] == 0.5556
    assert body["Description"] == "Rankine scale"


@respx.mock
def test_create_unit_server_error_raises() -> None:
    """create_unit raises ServerError on 500."""
    respx.post(f"{BASE}/unitclasses/{UC_WID}/units").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        with pytest.raises(ServerError):
            uc.create_unit(UC_WID, name="Bad", abbreviation="BAD")


# ===========================================================================
# Sync — update / delete
# ===========================================================================


@respx.mock
def test_update_happy_path() -> None:
    """update sends PATCH request."""
    route = respx.patch(f"{BASE}/unitclasses/{UC_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        uc.update(UC_WID, {"Description": "updated"})
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["Description"] == "updated"


@respx.mock
def test_delete_happy_path() -> None:
    """delete sends DELETE request."""
    route = respx.delete(f"{BASE}/unitclasses/{UC_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        uc.delete(UC_WID)
    assert route.called


# ===========================================================================
# Sync — get_unit_by_web_id / update_unit / delete_unit
# ===========================================================================


@respx.mock
def test_get_unit_by_web_id_happy_path() -> None:
    """get_unit_by_web_id returns a PIUnit."""
    respx.get(f"{BASE}/units/{UNIT_WID}").mock(
        return_value=httpx.Response(200, json=UNIT_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        result = uc.get_unit_by_web_id(UNIT_WID)
    assert isinstance(result, PIUnit)
    assert result.name == "degree Fahrenheit"


@respx.mock
def test_update_unit_happy_path() -> None:
    """update_unit sends PATCH request."""
    route = respx.patch(f"{BASE}/units/{UNIT_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        uc.update_unit(UNIT_WID, {"Description": "updated"})
    assert route.called


@respx.mock
def test_delete_unit_happy_path() -> None:
    """delete_unit sends DELETE request."""
    route = respx.delete(f"{BASE}/units/{UNIT_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        uc = _SyncUC(client)
        uc.delete_unit(UNIT_WID)
    assert route.called


# ===========================================================================
# Async — get_by_web_id
# ===========================================================================


@respx.mock
async def test_async_get_by_web_id_happy_path() -> None:
    """Async get_by_web_id returns a PIUnitClass."""
    respx.get(f"{BASE}/unitclasses/{UC_WID}").mock(
        return_value=httpx.Response(200, json=UC_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        result = await uc.get_by_web_id(UC_WID)
    assert isinstance(result, PIUnitClass)
    assert result.web_id == UC_WID


@respx.mock
async def test_async_get_by_web_id_404_raises() -> None:
    """Async get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/unitclasses/{UC_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        with pytest.raises(NotFoundError):
            await uc.get_by_web_id(UC_WID)


# ===========================================================================
# Async — get_by_path
# ===========================================================================


@respx.mock
async def test_async_get_by_path_happy_path() -> None:
    """Async get_by_path returns a PIUnitClass."""
    respx.get(f"{BASE}/unitclasses").mock(
        return_value=httpx.Response(200, json=UC_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        result = await uc.get_by_path("\\\\SERVER\\UnitClasses[Temperature]")
    assert isinstance(result, PIUnitClass)
    assert result.name == "Temperature"


# ===========================================================================
# Async — get_units
# ===========================================================================


@respx.mock
async def test_async_get_units_happy_path() -> None:
    """Async get_units returns a list of PIUnit."""
    respx.get(f"{BASE}/unitclasses/{UC_WID}/units").mock(
        return_value=httpx.Response(200, json=UNITS_LIST_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        units = await uc.get_units(UC_WID)
    assert len(units) == 2
    assert units[0].abbreviation == "degF"


@respx.mock
async def test_async_get_units_404_raises() -> None:
    """Async get_units raises NotFoundError on 404."""
    respx.get(f"{BASE}/unitclasses/{UC_WID}/units").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        with pytest.raises(NotFoundError):
            await uc.get_units(UC_WID)


# ===========================================================================
# Async — get_canonical_unit
# ===========================================================================


@respx.mock
async def test_async_get_canonical_unit_happy_path() -> None:
    """Async get_canonical_unit returns a PIUnit."""
    canonical = {
        "WebId": "UN0K001",
        "Name": "kelvin",
        "Abbreviation": "K",
        "Factor": 1.0,
        "Offset": 0.0,
        "Links": {},
    }
    respx.get(f"{BASE}/unitclasses/{UC_WID}/canonicalunit").mock(
        return_value=httpx.Response(200, json=canonical)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        result = await uc.get_canonical_unit(UC_WID)
    assert isinstance(result, PIUnit)
    assert result.abbreviation == "K"


# ===========================================================================
# Async — create_unit
# ===========================================================================


@respx.mock
async def test_async_create_unit_happy_path() -> None:
    """Async create_unit sends the correct POST body."""
    route = respx.post(f"{BASE}/unitclasses/{UC_WID}/units").mock(
        return_value=httpx.Response(201)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        await uc.create_unit(UC_WID, name="degR", abbreviation="degR")
    assert route.called


@respx.mock
async def test_async_create_unit_server_error_raises() -> None:
    """Async create_unit raises ServerError on 500."""
    respx.post(f"{BASE}/unitclasses/{UC_WID}/units").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        with pytest.raises(ServerError):
            await uc.create_unit(UC_WID, name="Bad", abbreviation="BAD")


# ===========================================================================
# Async — update / delete / unit CRUD
# ===========================================================================


@respx.mock
async def test_async_update_happy_path() -> None:
    """Async update sends PATCH request."""
    route = respx.patch(f"{BASE}/unitclasses/{UC_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        await uc.update(UC_WID, {"Description": "updated"})
    assert route.called


@respx.mock
async def test_async_delete_happy_path() -> None:
    """Async delete sends DELETE request."""
    route = respx.delete(f"{BASE}/unitclasses/{UC_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        await uc.delete(UC_WID)
    assert route.called


@respx.mock
async def test_async_get_unit_by_web_id_happy_path() -> None:
    """Async get_unit_by_web_id returns a PIUnit."""
    respx.get(f"{BASE}/units/{UNIT_WID}").mock(
        return_value=httpx.Response(200, json=UNIT_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        result = await uc.get_unit_by_web_id(UNIT_WID)
    assert isinstance(result, PIUnit)
    assert result.name == "degree Fahrenheit"


@respx.mock
async def test_async_update_unit_happy_path() -> None:
    """Async update_unit sends PATCH."""
    route = respx.patch(f"{BASE}/units/{UNIT_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        await uc.update_unit(UNIT_WID, {"Description": "updated"})
    assert route.called


@respx.mock
async def test_async_delete_unit_happy_path() -> None:
    """Async delete_unit sends DELETE."""
    route = respx.delete(f"{BASE}/units/{UNIT_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        uc = _AsyncUC(client)
        await uc.delete_unit(UNIT_WID)
    assert route.called
