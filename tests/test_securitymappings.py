"""Tests for SecurityMappings resource — sync and async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import NotFoundError, ServerError
from pisharp_piwebapi.models import PISecurityMapping
from pisharp_piwebapi.securitymappings import (
    AsyncSecurityMappingsMixin,
    SecurityMappingsMixin,
)

BASE = "https://piserver/piwebapi"
SM_WID = "SM0mapping001"
DS_WID = "DS001"

MAPPING_PAYLOAD = {
    "WebId": SM_WID,
    "Id": "guid-sm-001",
    "Name": "Mapping1",
    "Description": "Maps domain admins to piadmins",
    "Path": "\\\\PISERVER\\Security Mappings[Mapping1]",
    "Account": "DOMAIN\\PI Admins",
    "SecurityIdentityWebId": "SI0piadmins002",
    "SecurityIdentityName": "piadmins",
    "IsEnabled": True,
    "Links": {"Self": f"{BASE}/securitymappings/{SM_WID}"},
}

MAPPING_2 = {
    "WebId": "SM0mapping002",
    "Id": "guid-sm-002",
    "Name": "Mapping2",
    "Description": "Maps operators to pioperators",
    "Path": "\\\\PISERVER\\Security Mappings[Mapping2]",
    "Account": "DOMAIN\\Operators",
    "SecurityIdentityWebId": "SI0ops003",
    "SecurityIdentityName": "pioperators",
    "IsEnabled": True,
    "Links": {},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SyncSM(SecurityMappingsMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncSM(AsyncSecurityMappingsMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync tests
# ===========================================================================


@respx.mock
def test_get_by_web_id_happy_path() -> None:
    """get_by_web_id returns a PISecurityMapping."""
    respx.get(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(200, json=MAPPING_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        sm = _SyncSM(client)
        result = sm.get_by_web_id(SM_WID)
    assert isinstance(result, PISecurityMapping)
    assert result.web_id == SM_WID
    assert result.name == "Mapping1"
    assert result.account == "DOMAIN\\PI Admins"
    assert result.security_identity_name == "piadmins"
    assert result.is_enabled is True


@respx.mock
def test_get_by_web_id_404_raises() -> None:
    """get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        sm = _SyncSM(client)
        with pytest.raises(NotFoundError):
            sm.get_by_web_id(SM_WID)


@respx.mock
def test_get_by_web_id_with_selected_fields() -> None:
    """get_by_web_id forwards selectedFields parameter."""
    route = respx.get(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(200, json=MAPPING_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        sm = _SyncSM(client)
        sm.get_by_web_id(SM_WID, selected_fields="Name;WebId")
    assert route.called
    assert b"selectedFields=" in route.calls.last.request.url.query


@respx.mock
def test_get_by_path_happy_path() -> None:
    """get_by_path returns a PISecurityMapping."""
    route = respx.get(f"{BASE}/securitymappings").mock(
        return_value=httpx.Response(200, json=MAPPING_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        sm = _SyncSM(client)
        result = sm.get_by_path(
            "\\\\PISERVER\\Security Mappings[Mapping1]"
        )
    assert isinstance(result, PISecurityMapping)
    assert route.called
    assert b"path=" in route.calls.last.request.url.query


@respx.mock
def test_list_by_server_happy_path() -> None:
    """list_by_server returns a list of PISecurityMapping."""
    respx.get(
        f"{BASE}/dataservers/{DS_WID}/securitymappings"
    ).mock(
        return_value=httpx.Response(
            200, json={"Items": [MAPPING_PAYLOAD, MAPPING_2]}
        )
    )
    with httpx.Client(base_url=BASE) as client:
        sm = _SyncSM(client)
        results = sm.list_by_server(DS_WID)
    assert len(results) == 2
    assert all(isinstance(r, PISecurityMapping) for r in results)
    assert results[0].name == "Mapping1"
    assert results[1].name == "Mapping2"


@respx.mock
def test_list_by_server_empty() -> None:
    """list_by_server returns empty list when none exist."""
    respx.get(
        f"{BASE}/dataservers/{DS_WID}/securitymappings"
    ).mock(return_value=httpx.Response(200, json={"Items": []}))
    with httpx.Client(base_url=BASE) as client:
        sm = _SyncSM(client)
        results = sm.list_by_server(DS_WID)
    assert results == []


@respx.mock
def test_list_by_server_flat_array() -> None:
    """list_by_server handles flat array response (no Items wrapper)."""
    respx.get(
        f"{BASE}/dataservers/{DS_WID}/securitymappings"
    ).mock(
        return_value=httpx.Response(
            200, json=[MAPPING_PAYLOAD, MAPPING_2]
        )
    )
    with httpx.Client(base_url=BASE) as client:
        sm = _SyncSM(client)
        results = sm.list_by_server(DS_WID)
    assert len(results) == 2


@respx.mock
def test_update_happy_path() -> None:
    """update sends PATCH with correct body."""
    route = respx.patch(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        sm = _SyncSM(client)
        sm.update(SM_WID, {"Description": "updated"})
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["Description"] == "updated"


@respx.mock
def test_delete_happy_path() -> None:
    """delete sends DELETE."""
    route = respx.delete(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        sm = _SyncSM(client)
        sm.delete(SM_WID)
    assert route.called


@respx.mock
def test_delete_404_raises() -> None:
    """delete raises NotFoundError on 404."""
    respx.delete(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        sm = _SyncSM(client)
        with pytest.raises(NotFoundError):
            sm.delete(SM_WID)


@respx.mock
def test_delete_500_raises() -> None:
    """delete raises ServerError on 500."""
    respx.delete(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(
            500, json={"Message": "Internal error"}
        )
    )
    with httpx.Client(base_url=BASE) as client:
        sm = _SyncSM(client)
        with pytest.raises(ServerError):
            sm.delete(SM_WID)


# ===========================================================================
# Async tests
# ===========================================================================


@respx.mock
async def test_async_get_by_web_id_happy_path() -> None:
    """Async get_by_web_id returns a PISecurityMapping."""
    respx.get(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(200, json=MAPPING_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        sm = _AsyncSM(client)
        result = await sm.get_by_web_id(SM_WID)
    assert isinstance(result, PISecurityMapping)
    assert result.web_id == SM_WID


@respx.mock
async def test_async_get_by_web_id_404_raises() -> None:
    """Async get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        sm = _AsyncSM(client)
        with pytest.raises(NotFoundError):
            await sm.get_by_web_id(SM_WID)


@respx.mock
async def test_async_get_by_path_happy_path() -> None:
    """Async get_by_path returns a PISecurityMapping."""
    respx.get(f"{BASE}/securitymappings").mock(
        return_value=httpx.Response(200, json=MAPPING_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        sm = _AsyncSM(client)
        result = await sm.get_by_path("\\\\PISERVER\\SMs[Mapping1]")
    assert isinstance(result, PISecurityMapping)


@respx.mock
async def test_async_list_by_server_happy_path() -> None:
    """Async list_by_server returns a list of PISecurityMapping."""
    respx.get(
        f"{BASE}/dataservers/{DS_WID}/securitymappings"
    ).mock(
        return_value=httpx.Response(
            200, json={"Items": [MAPPING_PAYLOAD, MAPPING_2]}
        )
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        sm = _AsyncSM(client)
        results = await sm.list_by_server(DS_WID)
    assert len(results) == 2


@respx.mock
async def test_async_update_happy_path() -> None:
    """Async update sends PATCH."""
    route = respx.patch(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        sm = _AsyncSM(client)
        await sm.update(SM_WID, {"Description": "updated"})
    assert route.called


@respx.mock
async def test_async_delete_happy_path() -> None:
    """Async delete sends DELETE."""
    route = respx.delete(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        sm = _AsyncSM(client)
        await sm.delete(SM_WID)
    assert route.called


@respx.mock
async def test_async_delete_server_error_raises() -> None:
    """Async delete raises ServerError on 500."""
    respx.delete(f"{BASE}/securitymappings/{SM_WID}").mock(
        return_value=httpx.Response(
            500, json={"Message": "Server error"}
        )
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        sm = _AsyncSM(client)
        with pytest.raises(ServerError):
            await sm.delete(SM_WID)
