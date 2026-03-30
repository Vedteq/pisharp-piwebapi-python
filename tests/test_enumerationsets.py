"""Tests for EnumerationSets resource — sync and async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.enumerationsets import (
    AsyncEnumerationSetsMixin,
    EnumerationSetsMixin,
)
from pisharp_piwebapi.exceptions import NotFoundError, ServerError
from pisharp_piwebapi.models import EnumerationSet, EnumerationValue

BASE = "https://piserver/piwebapi"
ENUM_SET_WID = "ES0digital001"
DS_WID = "DS001"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

ENUM_SET_PAYLOAD = {
    "WebId": ENUM_SET_WID,
    "Id": "guid-es-001",
    "Name": "Modes",
    "Description": "Operating modes",
    "Path": "\\\\SERVER\\EnumerationSets[Modes]",
    "Links": {"Self": f"{BASE}/enumerationsets/{ENUM_SET_WID}"},
}

ENUM_VALUES_PAYLOAD = {
    "Items": [
        {
            "WebId": "EV001",
            "Id": "1",
            "Name": "Off",
            "Description": "System off",
            "Value": 0,
            "Path": "",
            "Links": {},
        },
        {
            "WebId": "EV002",
            "Id": "2",
            "Name": "Running",
            "Description": "System running",
            "Value": 1,
            "Path": "",
            "Links": {},
        },
        {
            "WebId": "EV003",
            "Id": "3",
            "Name": "Fault",
            "Description": "System fault",
            "Value": 2,
            "Path": "",
            "Links": {},
        },
    ]
}

ENUM_SETS_LIST_PAYLOAD = {
    "Items": [
        ENUM_SET_PAYLOAD,
        {
            "WebId": "ES0digital002",
            "Id": "guid-es-002",
            "Name": "Status",
            "Description": "Status codes",
            "Path": "",
            "Links": {},
        },
    ]
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SyncEnumSets(EnumerationSetsMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncEnumSets(AsyncEnumerationSetsMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_by_web_id
# ===========================================================================


@respx.mock
def test_get_by_web_id_happy_path() -> None:
    """get_by_web_id returns an EnumerationSet."""
    respx.get(f"{BASE}/enumerationsets/{ENUM_SET_WID}").mock(
        return_value=httpx.Response(200, json=ENUM_SET_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        es = _SyncEnumSets(client)
        result = es.get_by_web_id(ENUM_SET_WID)

    assert isinstance(result, EnumerationSet)
    assert result.web_id == ENUM_SET_WID
    assert result.name == "Modes"
    assert result.description == "Operating modes"


@respx.mock
def test_get_by_web_id_404_raises() -> None:
    """get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/enumerationsets/{ENUM_SET_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        es = _SyncEnumSets(client)
        with pytest.raises(NotFoundError):
            es.get_by_web_id(ENUM_SET_WID)


# ===========================================================================
# Sync — get_by_path
# ===========================================================================


@respx.mock
def test_get_by_path_happy_path() -> None:
    """get_by_path returns an EnumerationSet."""
    route = respx.get(f"{BASE}/enumerationsets").mock(
        return_value=httpx.Response(200, json=ENUM_SET_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        es = _SyncEnumSets(client)
        result = es.get_by_path("\\\\SERVER\\EnumerationSets[Modes]")

    assert isinstance(result, EnumerationSet)
    assert result.name == "Modes"
    assert route.called
    assert b"path=" in route.calls.last.request.url.query


# ===========================================================================
# Sync — get_values
# ===========================================================================


@respx.mock
def test_get_values_happy_path() -> None:
    """get_values returns a list of EnumerationValue."""
    respx.get(
        f"{BASE}/enumerationsets/{ENUM_SET_WID}/enumerationvalues"
    ).mock(return_value=httpx.Response(200, json=ENUM_VALUES_PAYLOAD))

    with httpx.Client(base_url=BASE) as client:
        es = _SyncEnumSets(client)
        values = es.get_values(ENUM_SET_WID)

    assert len(values) == 3
    assert all(isinstance(v, EnumerationValue) for v in values)
    assert values[0].name == "Off"
    assert values[0].value == 0
    assert values[1].name == "Running"
    assert values[1].value == 1
    assert values[2].name == "Fault"


@respx.mock
def test_get_values_404_raises() -> None:
    """get_values raises NotFoundError on 404."""
    respx.get(
        f"{BASE}/enumerationsets/{ENUM_SET_WID}/enumerationvalues"
    ).mock(return_value=httpx.Response(404, json={"Message": "Not found"}))

    with httpx.Client(base_url=BASE) as client:
        es = _SyncEnumSets(client)
        with pytest.raises(NotFoundError):
            es.get_values(ENUM_SET_WID)


# ===========================================================================
# Sync — get_by_data_server
# ===========================================================================


@respx.mock
def test_get_by_data_server_happy_path() -> None:
    """get_by_data_server returns a list of EnumerationSet."""
    respx.get(f"{BASE}/dataservers/{DS_WID}/enumerationsets").mock(
        return_value=httpx.Response(200, json=ENUM_SETS_LIST_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        es = _SyncEnumSets(client)
        sets = es.get_by_data_server(DS_WID)

    assert len(sets) == 2
    assert all(isinstance(s, EnumerationSet) for s in sets)
    assert sets[0].name == "Modes"
    assert sets[1].name == "Status"


@respx.mock
def test_get_by_data_server_404_raises() -> None:
    """get_by_data_server raises NotFoundError on 404."""
    respx.get(f"{BASE}/dataservers/{DS_WID}/enumerationsets").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        es = _SyncEnumSets(client)
        with pytest.raises(NotFoundError):
            es.get_by_data_server(DS_WID)


# ===========================================================================
# Sync — create_value
# ===========================================================================


@respx.mock
def test_create_value_happy_path() -> None:
    """create_value sends the correct POST body."""
    route = respx.post(
        f"{BASE}/enumerationsets/{ENUM_SET_WID}/enumerationvalues"
    ).mock(return_value=httpx.Response(201))

    with httpx.Client(base_url=BASE) as client:
        es = _SyncEnumSets(client)
        es.create_value(ENUM_SET_WID, name="Standby", value=3, description="Idle")

    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["Name"] == "Standby"
    assert body["Value"] == 3
    assert body["Description"] == "Idle"


@respx.mock
def test_create_value_server_error_raises() -> None:
    """create_value raises ServerError on 500."""
    respx.post(
        f"{BASE}/enumerationsets/{ENUM_SET_WID}/enumerationvalues"
    ).mock(return_value=httpx.Response(500, json={"Message": "Server error"}))

    with httpx.Client(base_url=BASE) as client:
        es = _SyncEnumSets(client)
        with pytest.raises(ServerError):
            es.create_value(ENUM_SET_WID, name="Bad", value=99)


# ===========================================================================
# Async — get_by_web_id
# ===========================================================================


@respx.mock
async def test_async_get_by_web_id_happy_path() -> None:
    """Async get_by_web_id returns an EnumerationSet."""
    respx.get(f"{BASE}/enumerationsets/{ENUM_SET_WID}").mock(
        return_value=httpx.Response(200, json=ENUM_SET_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        es = _AsyncEnumSets(client)
        result = await es.get_by_web_id(ENUM_SET_WID)

    assert isinstance(result, EnumerationSet)
    assert result.web_id == ENUM_SET_WID


@respx.mock
async def test_async_get_by_web_id_404_raises() -> None:
    """Async get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/enumerationsets/{ENUM_SET_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        es = _AsyncEnumSets(client)
        with pytest.raises(NotFoundError):
            await es.get_by_web_id(ENUM_SET_WID)


# ===========================================================================
# Async — get_values
# ===========================================================================


@respx.mock
async def test_async_get_values_happy_path() -> None:
    """Async get_values returns a list of EnumerationValue."""
    respx.get(
        f"{BASE}/enumerationsets/{ENUM_SET_WID}/enumerationvalues"
    ).mock(return_value=httpx.Response(200, json=ENUM_VALUES_PAYLOAD))

    async with httpx.AsyncClient(base_url=BASE) as client:
        es = _AsyncEnumSets(client)
        values = await es.get_values(ENUM_SET_WID)

    assert len(values) == 3
    assert values[0].name == "Off"


@respx.mock
async def test_async_get_values_404_raises() -> None:
    """Async get_values raises NotFoundError on 404."""
    respx.get(
        f"{BASE}/enumerationsets/{ENUM_SET_WID}/enumerationvalues"
    ).mock(return_value=httpx.Response(404, json={"Message": "Not found"}))

    async with httpx.AsyncClient(base_url=BASE) as client:
        es = _AsyncEnumSets(client)
        with pytest.raises(NotFoundError):
            await es.get_values(ENUM_SET_WID)


# ===========================================================================
# Async — get_by_data_server
# ===========================================================================


@respx.mock
async def test_async_get_by_data_server_happy_path() -> None:
    """Async get_by_data_server returns a list of EnumerationSet."""
    respx.get(f"{BASE}/dataservers/{DS_WID}/enumerationsets").mock(
        return_value=httpx.Response(200, json=ENUM_SETS_LIST_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        es = _AsyncEnumSets(client)
        sets = await es.get_by_data_server(DS_WID)

    assert len(sets) == 2


# ===========================================================================
# Async — create_value
# ===========================================================================


@respx.mock
async def test_async_create_value_happy_path() -> None:
    """Async create_value sends the correct POST body."""
    route = respx.post(
        f"{BASE}/enumerationsets/{ENUM_SET_WID}/enumerationvalues"
    ).mock(return_value=httpx.Response(201))

    async with httpx.AsyncClient(base_url=BASE) as client:
        es = _AsyncEnumSets(client)
        await es.create_value(ENUM_SET_WID, name="Standby", value=3)

    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["Name"] == "Standby"
    assert body["Value"] == 3


@respx.mock
async def test_async_create_value_server_error_raises() -> None:
    """Async create_value raises ServerError on 500."""
    respx.post(
        f"{BASE}/enumerationsets/{ENUM_SET_WID}/enumerationvalues"
    ).mock(return_value=httpx.Response(500, json={"Message": "Server error"}))

    async with httpx.AsyncClient(base_url=BASE) as client:
        es = _AsyncEnumSets(client)
        with pytest.raises(ServerError):
            await es.create_value(ENUM_SET_WID, name="Bad", value=99)
