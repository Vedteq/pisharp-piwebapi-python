"""Tests for TimeRules resource — sync and async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import NotFoundError, ServerError
from pisharp_piwebapi.models import TimeRule
from pisharp_piwebapi.timerules import AsyncTimeRulesMixin, TimeRulesMixin

BASE = "https://piserver/piwebapi"
TR_WID = "T1AbPeriodic001"
AN_WID = "AN0flowcalc001"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

TR_PAYLOAD = {
    "WebId": TR_WID,
    "Id": "guid-tr-001",
    "Name": "Periodic",
    "Description": "",
    "Path": "\\\\AF_SERVER\\DB\\Element|Analysis\\TimeRule",
    "ConfigString": "Frequency=300",
    "ConfigStringStored": "Frequency=300",
    "DisplayString": "Every 300 seconds",
    "EditorType": "Periodic",
    "IsConfigured": True,
    "IsInitializing": False,
    "MergeDuplicatedItems": False,
    "PlugInName": "Periodic",
    "Links": {"Self": f"{BASE}/timerules/{TR_WID}"},
}

TR_LIST_PAYLOAD = {"Items": [TR_PAYLOAD]}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SyncTR(TimeRulesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncTR(AsyncTimeRulesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ========================== SYNC TESTS ==========================


class TestTimeRulesSync:
    """Sync happy-path tests for TimeRules."""

    @respx.mock
    def test_get_by_web_id_happy_path(self) -> None:
        respx.get(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(200, json=TR_PAYLOAD)
        )
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        result = tr.get_by_web_id(TR_WID)
        assert isinstance(result, TimeRule)
        assert result.web_id == TR_WID
        assert result.name == "Periodic"
        assert result.plug_in_name == "Periodic"
        assert result.config_string == "Frequency=300"
        client.close()

    @respx.mock
    def test_get_by_web_id_selected_fields(self) -> None:
        respx.get(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(200, json=TR_PAYLOAD)
        )
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        result = tr.get_by_web_id(TR_WID, selected_fields="WebId;Name")
        assert result.web_id == TR_WID
        req = respx.calls.last.request
        assert "selectedFields" in str(req.url)
        client.close()

    @respx.mock
    def test_get_by_analysis_happy_path(self) -> None:
        respx.get(f"{BASE}/analyses/{AN_WID}/timerules").mock(
            return_value=httpx.Response(200, json=TR_LIST_PAYLOAD)
        )
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        result = tr.get_by_analysis(AN_WID)
        assert len(result) == 1
        assert result[0].plug_in_name == "Periodic"
        client.close()

    @respx.mock
    def test_get_by_analysis_empty(self) -> None:
        respx.get(f"{BASE}/analyses/{AN_WID}/timerules").mock(
            return_value=httpx.Response(200, json={"Items": []})
        )
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        result = tr.get_by_analysis(AN_WID)
        assert result == []
        client.close()

    @respx.mock
    def test_create_on_analysis_happy_path(self) -> None:
        respx.post(f"{BASE}/analyses/{AN_WID}/timerules").mock(
            return_value=httpx.Response(201)
        )
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        tr.create_on_analysis(
            AN_WID,
            {"Name": "Periodic", "PlugInName": "Periodic", "ConfigString": "Frequency=60"},
        )
        body = json.loads(respx.calls.last.request.content)
        assert body["PlugInName"] == "Periodic"
        client.close()

    @respx.mock
    def test_update_happy_path(self) -> None:
        respx.patch(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(204)
        )
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        tr.update(TR_WID, {"ConfigString": "Frequency=60"})
        body = json.loads(respx.calls.last.request.content)
        assert body["ConfigString"] == "Frequency=60"
        client.close()

    @respx.mock
    def test_delete_happy_path(self) -> None:
        respx.delete(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(204)
        )
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        tr.delete(TR_WID)
        assert respx.calls.last.request.method == "DELETE"
        client.close()


class TestTimeRulesSyncErrors:
    """Sync error-path tests for TimeRules."""

    @respx.mock
    def test_get_by_web_id_not_found(self) -> None:
        respx.get(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(404, json={"Errors": ["Not found"]})
        )
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        with pytest.raises(NotFoundError):
            tr.get_by_web_id(TR_WID)
        client.close()

    @respx.mock
    def test_delete_server_error(self) -> None:
        respx.delete(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(500, json={"Errors": ["Internal"]})
        )
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        with pytest.raises(ServerError):
            tr.delete(TR_WID)
        client.close()

    def test_get_by_web_id_invalid_web_id(self) -> None:
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        with pytest.raises(ValueError, match="web_id"):
            tr.get_by_web_id("")
        client.close()

    def test_get_by_analysis_invalid_web_id(self) -> None:
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        with pytest.raises(ValueError, match="analysis_web_id"):
            tr.get_by_analysis("")
        client.close()

    @respx.mock
    def test_update_not_found(self) -> None:
        respx.patch(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(404, json={"Errors": ["Not found"]})
        )
        client = httpx.Client(base_url=BASE)
        tr = _SyncTR(client)
        with pytest.raises(NotFoundError):
            tr.update(TR_WID, {"ConfigString": "Frequency=1"})
        client.close()


# ========================== ASYNC TESTS ==========================


class TestTimeRulesAsync:
    """Async happy-path tests for TimeRules."""

    @respx.mock
    async def test_get_by_web_id_happy_path(self) -> None:
        respx.get(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(200, json=TR_PAYLOAD)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            tr = _AsyncTR(client)
            result = await tr.get_by_web_id(TR_WID)
            assert isinstance(result, TimeRule)
            assert result.web_id == TR_WID
            assert result.plug_in_name == "Periodic"

    @respx.mock
    async def test_get_by_analysis_happy_path(self) -> None:
        respx.get(f"{BASE}/analyses/{AN_WID}/timerules").mock(
            return_value=httpx.Response(200, json=TR_LIST_PAYLOAD)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            tr = _AsyncTR(client)
            result = await tr.get_by_analysis(AN_WID)
            assert len(result) == 1

    @respx.mock
    async def test_create_on_analysis_happy_path(self) -> None:
        respx.post(f"{BASE}/analyses/{AN_WID}/timerules").mock(
            return_value=httpx.Response(201)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            tr = _AsyncTR(client)
            await tr.create_on_analysis(
                AN_WID,
                {"Name": "Periodic", "PlugInName": "Periodic"},
            )

    @respx.mock
    async def test_update_happy_path(self) -> None:
        respx.patch(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(204)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            tr = _AsyncTR(client)
            await tr.update(TR_WID, {"ConfigString": "Frequency=60"})

    @respx.mock
    async def test_delete_happy_path(self) -> None:
        respx.delete(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(204)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            tr = _AsyncTR(client)
            await tr.delete(TR_WID)


class TestTimeRulesAsyncErrors:
    """Async error-path tests for TimeRules."""

    @respx.mock
    async def test_get_by_web_id_not_found(self) -> None:
        respx.get(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(404, json={"Errors": ["Not found"]})
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            tr = _AsyncTR(client)
            with pytest.raises(NotFoundError):
                await tr.get_by_web_id(TR_WID)

    @respx.mock
    async def test_delete_server_error(self) -> None:
        respx.delete(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(500, json={"Errors": ["Internal"]})
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            tr = _AsyncTR(client)
            with pytest.raises(ServerError):
                await tr.delete(TR_WID)

    @respx.mock
    async def test_update_not_found(self) -> None:
        respx.patch(f"{BASE}/timerules/{TR_WID}").mock(
            return_value=httpx.Response(404, json={"Errors": ["Not found"]})
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            tr = _AsyncTR(client)
            with pytest.raises(NotFoundError):
                await tr.update(TR_WID, {"ConfigString": "Frequency=1"})
