"""Tests for SecurityIdentities resource — sync and async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import NotFoundError, ServerError
from pisharp_piwebapi.models import PISecurityIdentity
from pisharp_piwebapi.securityidentities import (
    AsyncSecurityIdentitiesMixin,
    SecurityIdentitiesMixin,
)

BASE = "https://piserver/piwebapi"
SI_WID = "SI0piworld001"
DS_WID = "DS001"

IDENTITY_PAYLOAD = {
    "WebId": SI_WID,
    "Id": "guid-si-001",
    "Name": "piworld",
    "Description": "Default PI World identity",
    "Path": "\\\\PISERVER\\Security Identities[piworld]",
    "IsEnabled": True,
    "Links": {"Self": f"{BASE}/securityidentities/{SI_WID}"},
}

IDENTITY_2 = {
    "WebId": "SI0piadmins002",
    "Id": "guid-si-002",
    "Name": "piadmins",
    "Description": "Administrators identity",
    "Path": "\\\\PISERVER\\Security Identities[piadmins]",
    "IsEnabled": True,
    "Links": {},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SyncSI(SecurityIdentitiesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncSI(AsyncSecurityIdentitiesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync tests
# ===========================================================================


@respx.mock
def test_get_by_web_id_happy_path() -> None:
    """get_by_web_id returns a PISecurityIdentity."""
    respx.get(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(200, json=IDENTITY_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        si = _SyncSI(client)
        result = si.get_by_web_id(SI_WID)
    assert isinstance(result, PISecurityIdentity)
    assert result.web_id == SI_WID
    assert result.name == "piworld"
    assert result.is_enabled is True


@respx.mock
def test_get_by_web_id_404_raises() -> None:
    """get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        si = _SyncSI(client)
        with pytest.raises(NotFoundError):
            si.get_by_web_id(SI_WID)


@respx.mock
def test_get_by_web_id_with_selected_fields() -> None:
    """get_by_web_id forwards selectedFields parameter."""
    route = respx.get(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(200, json=IDENTITY_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        si = _SyncSI(client)
        si.get_by_web_id(SI_WID, selected_fields="Name;WebId")
    assert route.called
    assert b"selectedFields=" in route.calls.last.request.url.query


@respx.mock
def test_get_by_path_happy_path() -> None:
    """get_by_path returns a PISecurityIdentity."""
    route = respx.get(f"{BASE}/securityidentities").mock(
        return_value=httpx.Response(200, json=IDENTITY_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        si = _SyncSI(client)
        result = si.get_by_path(
            "\\\\PISERVER\\Security Identities[piworld]"
        )
    assert isinstance(result, PISecurityIdentity)
    assert route.called
    assert b"path=" in route.calls.last.request.url.query


@respx.mock
def test_get_by_name_happy_path() -> None:
    """get_by_name returns a PISecurityIdentity from a data server."""
    route = respx.get(
        f"{BASE}/dataservers/{DS_WID}/securityidentities"
    ).mock(return_value=httpx.Response(200, json=IDENTITY_PAYLOAD))
    with httpx.Client(base_url=BASE) as client:
        si = _SyncSI(client)
        result = si.get_by_name(DS_WID, "piworld")
    assert isinstance(result, PISecurityIdentity)
    assert result.name == "piworld"
    assert route.called
    assert b"name=" in route.calls.last.request.url.query


@respx.mock
def test_list_by_server_happy_path() -> None:
    """list_by_server returns a list of PISecurityIdentity."""
    respx.get(
        f"{BASE}/dataservers/{DS_WID}/securityidentities"
    ).mock(
        return_value=httpx.Response(
            200, json={"Items": [IDENTITY_PAYLOAD, IDENTITY_2]}
        )
    )
    with httpx.Client(base_url=BASE) as client:
        si = _SyncSI(client)
        results = si.list_by_server(DS_WID)
    assert len(results) == 2
    assert all(isinstance(r, PISecurityIdentity) for r in results)
    assert results[0].name == "piworld"
    assert results[1].name == "piadmins"


@respx.mock
def test_list_by_server_empty() -> None:
    """list_by_server returns empty list when no identities exist."""
    respx.get(
        f"{BASE}/dataservers/{DS_WID}/securityidentities"
    ).mock(return_value=httpx.Response(200, json={"Items": []}))
    with httpx.Client(base_url=BASE) as client:
        si = _SyncSI(client)
        results = si.list_by_server(DS_WID)
    assert results == []


@respx.mock
def test_update_happy_path() -> None:
    """update sends PATCH with correct body."""
    route = respx.patch(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        si = _SyncSI(client)
        si.update(SI_WID, {"Description": "updated", "IsEnabled": False})
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["Description"] == "updated"
    assert body["IsEnabled"] is False


@respx.mock
def test_delete_happy_path() -> None:
    """delete sends DELETE."""
    route = respx.delete(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        si = _SyncSI(client)
        si.delete(SI_WID)
    assert route.called


@respx.mock
def test_delete_404_raises() -> None:
    """delete raises NotFoundError on 404."""
    respx.delete(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        si = _SyncSI(client)
        with pytest.raises(NotFoundError):
            si.delete(SI_WID)


@respx.mock
def test_delete_500_raises() -> None:
    """delete raises ServerError on 500."""
    respx.delete(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(
            500, json={"Message": "Internal error"}
        )
    )
    with httpx.Client(base_url=BASE) as client:
        si = _SyncSI(client)
        with pytest.raises(ServerError):
            si.delete(SI_WID)


# ===========================================================================
# Async tests
# ===========================================================================


@respx.mock
async def test_async_get_by_web_id_happy_path() -> None:
    """Async get_by_web_id returns a PISecurityIdentity."""
    respx.get(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(200, json=IDENTITY_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        si = _AsyncSI(client)
        result = await si.get_by_web_id(SI_WID)
    assert isinstance(result, PISecurityIdentity)
    assert result.web_id == SI_WID


@respx.mock
async def test_async_get_by_web_id_404_raises() -> None:
    """Async get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        si = _AsyncSI(client)
        with pytest.raises(NotFoundError):
            await si.get_by_web_id(SI_WID)


@respx.mock
async def test_async_get_by_path_happy_path() -> None:
    """Async get_by_path returns a PISecurityIdentity."""
    respx.get(f"{BASE}/securityidentities").mock(
        return_value=httpx.Response(200, json=IDENTITY_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        si = _AsyncSI(client)
        result = await si.get_by_path("\\\\PISERVER\\SIs[piworld]")
    assert isinstance(result, PISecurityIdentity)


@respx.mock
async def test_async_get_by_name_happy_path() -> None:
    """Async get_by_name returns a PISecurityIdentity."""
    respx.get(
        f"{BASE}/dataservers/{DS_WID}/securityidentities"
    ).mock(return_value=httpx.Response(200, json=IDENTITY_PAYLOAD))
    async with httpx.AsyncClient(base_url=BASE) as client:
        si = _AsyncSI(client)
        result = await si.get_by_name(DS_WID, "piworld")
    assert result.name == "piworld"


@respx.mock
async def test_async_list_by_server_happy_path() -> None:
    """Async list_by_server returns a list of PISecurityIdentity."""
    respx.get(
        f"{BASE}/dataservers/{DS_WID}/securityidentities"
    ).mock(
        return_value=httpx.Response(
            200, json={"Items": [IDENTITY_PAYLOAD, IDENTITY_2]}
        )
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        si = _AsyncSI(client)
        results = await si.list_by_server(DS_WID)
    assert len(results) == 2


@respx.mock
async def test_async_update_happy_path() -> None:
    """Async update sends PATCH."""
    route = respx.patch(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        si = _AsyncSI(client)
        await si.update(SI_WID, {"Description": "updated"})
    assert route.called


@respx.mock
async def test_async_delete_happy_path() -> None:
    """Async delete sends DELETE."""
    route = respx.delete(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        si = _AsyncSI(client)
        await si.delete(SI_WID)
    assert route.called


@respx.mock
async def test_async_delete_500_raises() -> None:
    """Async delete raises ServerError on 500."""
    respx.delete(f"{BASE}/securityidentities/{SI_WID}").mock(
        return_value=httpx.Response(
            500, json={"Message": "Server error"}
        )
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        si = _AsyncSI(client)
        with pytest.raises(ServerError):
            await si.delete(SI_WID)
