"""Tests for EnumerationValues resource — sync and async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.enumerationvalues import (
    AsyncEnumerationValuesMixin,
    EnumerationValuesMixin,
)
from pisharp_piwebapi.exceptions import NotFoundError, ServerError
from pisharp_piwebapi.models import EnumerationValue

BASE = "https://piserver/piwebapi"
EV_WID = "E1AbRunning001"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

EV_PAYLOAD = {
    "WebId": EV_WID,
    "Id": "guid-ev-001",
    "Name": "Running",
    "Description": "Equipment is running",
    "Value": 1,
    "Path": "\\\\AF_SERVER\\DB\\EnumSets[EquipStatus]\\Running",
    "Links": {"Self": f"{BASE}/enumerationvalues/{EV_WID}"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SyncEV(EnumerationValuesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncEV(AsyncEnumerationValuesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ========================== SYNC TESTS ==========================


class TestEnumerationValuesSync:
    """Sync happy-path tests for EnumerationValues."""

    @respx.mock
    def test_get_by_web_id_happy_path(self) -> None:
        respx.get(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(200, json=EV_PAYLOAD)
        )
        client = httpx.Client(base_url=BASE)
        ev = _SyncEV(client)
        result = ev.get_by_web_id(EV_WID)
        assert isinstance(result, EnumerationValue)
        assert result.web_id == EV_WID
        assert result.name == "Running"
        assert result.value == 1
        client.close()

    @respx.mock
    def test_get_by_web_id_selected_fields(self) -> None:
        respx.get(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(200, json=EV_PAYLOAD)
        )
        client = httpx.Client(base_url=BASE)
        ev = _SyncEV(client)
        result = ev.get_by_web_id(EV_WID, selected_fields="WebId;Name")
        assert result.web_id == EV_WID
        req = respx.calls.last.request
        assert "selectedFields" in str(req.url)
        client.close()

    @respx.mock
    def test_get_by_path_happy_path(self) -> None:
        respx.get(f"{BASE}/enumerationvalues").mock(
            return_value=httpx.Response(200, json=EV_PAYLOAD)
        )
        client = httpx.Client(base_url=BASE)
        ev = _SyncEV(client)
        result = ev.get_by_path(
            "\\\\AF_SERVER\\DB\\EnumSets[EquipStatus]\\Running"
        )
        assert result.name == "Running"
        req = respx.calls.last.request
        assert "path" in str(req.url)
        client.close()

    @respx.mock
    def test_update_happy_path(self) -> None:
        respx.patch(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(204)
        )
        client = httpx.Client(base_url=BASE)
        ev = _SyncEV(client)
        ev.update(EV_WID, {"Description": "Updated description"})
        body = json.loads(respx.calls.last.request.content)
        assert body["Description"] == "Updated description"
        client.close()

    @respx.mock
    def test_delete_happy_path(self) -> None:
        respx.delete(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(204)
        )
        client = httpx.Client(base_url=BASE)
        ev = _SyncEV(client)
        ev.delete(EV_WID)
        assert respx.calls.last.request.method == "DELETE"
        client.close()


class TestEnumerationValuesSyncErrors:
    """Sync error-path tests for EnumerationValues."""

    @respx.mock
    def test_get_by_web_id_not_found(self) -> None:
        respx.get(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        client = httpx.Client(base_url=BASE)
        ev = _SyncEV(client)
        with pytest.raises(NotFoundError):
            ev.get_by_web_id(EV_WID)
        client.close()

    @respx.mock
    def test_get_by_path_not_found(self) -> None:
        respx.get(f"{BASE}/enumerationvalues").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        client = httpx.Client(base_url=BASE)
        ev = _SyncEV(client)
        with pytest.raises(NotFoundError):
            ev.get_by_path("\\\\BAD\\PATH")
        client.close()

    @respx.mock
    def test_delete_server_error(self) -> None:
        respx.delete(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(
                500, json={"Errors": ["Internal"]}
            )
        )
        client = httpx.Client(base_url=BASE)
        ev = _SyncEV(client)
        with pytest.raises(ServerError):
            ev.delete(EV_WID)
        client.close()

    def test_get_by_web_id_invalid_web_id(self) -> None:
        client = httpx.Client(base_url=BASE)
        ev = _SyncEV(client)
        with pytest.raises(ValueError, match="web_id"):
            ev.get_by_web_id("")
        client.close()

    @respx.mock
    def test_update_not_found(self) -> None:
        respx.patch(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        client = httpx.Client(base_url=BASE)
        ev = _SyncEV(client)
        with pytest.raises(NotFoundError):
            ev.update(EV_WID, {"Description": "x"})
        client.close()


# ========================== ASYNC TESTS ==========================


class TestEnumerationValuesAsync:
    """Async happy-path tests for EnumerationValues."""

    @respx.mock
    async def test_get_by_web_id_happy_path(self) -> None:
        respx.get(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(200, json=EV_PAYLOAD)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ev = _AsyncEV(client)
            result = await ev.get_by_web_id(EV_WID)
            assert isinstance(result, EnumerationValue)
            assert result.web_id == EV_WID
            assert result.value == 1

    @respx.mock
    async def test_get_by_path_happy_path(self) -> None:
        respx.get(f"{BASE}/enumerationvalues").mock(
            return_value=httpx.Response(200, json=EV_PAYLOAD)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ev = _AsyncEV(client)
            result = await ev.get_by_path(
                "\\\\AF_SERVER\\DB\\EnumSets[EquipStatus]\\Running"
            )
            assert result.name == "Running"

    @respx.mock
    async def test_update_happy_path(self) -> None:
        respx.patch(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(204)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ev = _AsyncEV(client)
            await ev.update(EV_WID, {"Description": "Updated"})

    @respx.mock
    async def test_delete_happy_path(self) -> None:
        respx.delete(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(204)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ev = _AsyncEV(client)
            await ev.delete(EV_WID)


class TestEnumerationValuesAsyncErrors:
    """Async error-path tests for EnumerationValues."""

    @respx.mock
    async def test_get_by_web_id_not_found(self) -> None:
        respx.get(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ev = _AsyncEV(client)
            with pytest.raises(NotFoundError):
                await ev.get_by_web_id(EV_WID)

    @respx.mock
    async def test_delete_server_error(self) -> None:
        respx.delete(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(
                500, json={"Errors": ["Internal"]}
            )
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ev = _AsyncEV(client)
            with pytest.raises(ServerError):
                await ev.delete(EV_WID)

    @respx.mock
    async def test_update_not_found(self) -> None:
        respx.patch(f"{BASE}/enumerationvalues/{EV_WID}").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ev = _AsyncEV(client)
            with pytest.raises(NotFoundError):
                await ev.update(EV_WID, {"Description": "x"})
