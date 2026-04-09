"""Tests for AnalysisRules resource — sync and async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.analysisrules import (
    AnalysisRulesMixin,
    AsyncAnalysisRulesMixin,
)
from pisharp_piwebapi.exceptions import NotFoundError, ServerError
from pisharp_piwebapi.models import PIAnalysisRule

BASE = "https://piserver/piwebapi"
AR_WID = "R1AbExpression001"
AN_WID = "AN0flowcalc001"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

AR_PAYLOAD = {
    "WebId": AR_WID,
    "Id": "guid-ar-001",
    "Name": "Expression1",
    "Description": "Flow calculation expression",
    "Path": "\\\\AF_SERVER\\DB\\Element|Analysis\\AnalysisRule",
    "ConfigString": "variable1 := 'sinusoid'; Out := variable1 + 1;",
    "DisplayString": "'sinusoid' + 1",
    "EditorType": "Expression",
    "HasChildren": False,
    "IsConfigured": True,
    "IsInitializing": False,
    "PlugInName": "PerformanceEquation",
    "VariableMapping": "variable1|\\\\SERVER\\sinusoid",
    "Links": {"Self": f"{BASE}/analysisrules/{AR_WID}"},
}

AR_CHILD_PAYLOAD = {
    "WebId": "R1AbChild001",
    "Id": "guid-ar-002",
    "Name": "ChildExpr",
    "Description": "",
    "Path": "",
    "ConfigString": "",
    "DisplayString": "",
    "EditorType": "Expression",
    "HasChildren": False,
    "IsConfigured": False,
    "IsInitializing": False,
    "PlugInName": "PerformanceEquation",
    "VariableMapping": "",
    "Links": {},
}

AR_LIST_PAYLOAD = {"Items": [AR_PAYLOAD, AR_CHILD_PAYLOAD]}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SyncAR(AnalysisRulesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncAR(AsyncAnalysisRulesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ========================== SYNC TESTS ==========================


class TestAnalysisRulesSync:
    """Sync happy-path tests for AnalysisRules."""

    @respx.mock
    def test_get_by_web_id_happy_path(self) -> None:
        respx.get(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(200, json=AR_PAYLOAD)
        )
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        result = ar.get_by_web_id(AR_WID)
        assert isinstance(result, PIAnalysisRule)
        assert result.web_id == AR_WID
        assert result.name == "Expression1"
        assert result.plug_in_name == "PerformanceEquation"
        assert result.config_string.startswith("variable1")
        client.close()

    @respx.mock
    def test_get_by_web_id_selected_fields(self) -> None:
        respx.get(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(200, json=AR_PAYLOAD)
        )
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        result = ar.get_by_web_id(AR_WID, selected_fields="WebId;Name")
        assert result.web_id == AR_WID
        req = respx.calls.last.request
        assert "selectedFields" in str(req.url)
        client.close()

    @respx.mock
    def test_get_children_happy_path(self) -> None:
        respx.get(
            f"{BASE}/analysisrules/{AR_WID}/analysisrules"
        ).mock(return_value=httpx.Response(200, json=AR_LIST_PAYLOAD))
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        result = ar.get_children(AR_WID)
        assert len(result) == 2
        assert all(isinstance(r, PIAnalysisRule) for r in result)
        client.close()

    @respx.mock
    def test_get_children_empty(self) -> None:
        respx.get(
            f"{BASE}/analysisrules/{AR_WID}/analysisrules"
        ).mock(return_value=httpx.Response(200, json={"Items": []}))
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        result = ar.get_children(AR_WID)
        assert result == []
        client.close()

    @respx.mock
    def test_create_child_happy_path(self) -> None:
        respx.post(
            f"{BASE}/analysisrules/{AR_WID}/analysisrules"
        ).mock(return_value=httpx.Response(201))
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        ar.create_child(AR_WID, {"Name": "NewChild", "PlugInName": "PerformanceEquation"})
        assert respx.calls.last.request.method == "POST"
        body = json.loads(respx.calls.last.request.content)
        assert body["Name"] == "NewChild"
        client.close()

    @respx.mock
    def test_get_by_analysis_happy_path(self) -> None:
        respx.get(
            f"{BASE}/analyses/{AN_WID}/analysisrules"
        ).mock(return_value=httpx.Response(200, json=AR_LIST_PAYLOAD))
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        result = ar.get_by_analysis(AN_WID)
        assert len(result) == 2
        client.close()

    @respx.mock
    def test_create_on_analysis_happy_path(self) -> None:
        respx.post(
            f"{BASE}/analyses/{AN_WID}/analysisrules"
        ).mock(return_value=httpx.Response(201))
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        ar.create_on_analysis(
            AN_WID, {"Name": "Root", "PlugInName": "PerformanceEquation"}
        )
        assert respx.calls.last.request.method == "POST"
        client.close()

    @respx.mock
    def test_update_happy_path(self) -> None:
        respx.patch(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(204)
        )
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        ar.update(AR_WID, {"ConfigString": "Out := 42;"})
        body = json.loads(respx.calls.last.request.content)
        assert body["ConfigString"] == "Out := 42;"
        client.close()

    @respx.mock
    def test_delete_happy_path(self) -> None:
        respx.delete(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(204)
        )
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        ar.delete(AR_WID)
        assert respx.calls.last.request.method == "DELETE"
        client.close()


class TestAnalysisRulesSyncErrors:
    """Sync error-path tests for AnalysisRules."""

    @respx.mock
    def test_get_by_web_id_not_found(self) -> None:
        respx.get(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        with pytest.raises(NotFoundError):
            ar.get_by_web_id(AR_WID)
        client.close()

    @respx.mock
    def test_delete_server_error(self) -> None:
        respx.delete(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(
                500, json={"Errors": ["Internal error"]}
            )
        )
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        with pytest.raises(ServerError):
            ar.delete(AR_WID)
        client.close()

    def test_get_by_web_id_invalid_web_id(self) -> None:
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        with pytest.raises(ValueError, match="web_id"):
            ar.get_by_web_id("")
        client.close()

    def test_get_by_analysis_invalid_web_id(self) -> None:
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        with pytest.raises(ValueError, match="analysis_web_id"):
            ar.get_by_analysis("")
        client.close()

    @respx.mock
    def test_update_not_found(self) -> None:
        respx.patch(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        client = httpx.Client(base_url=BASE)
        ar = _SyncAR(client)
        with pytest.raises(NotFoundError):
            ar.update(AR_WID, {"ConfigString": "x"})
        client.close()


# ========================== ASYNC TESTS ==========================


class TestAnalysisRulesAsync:
    """Async happy-path tests for AnalysisRules."""

    @respx.mock
    async def test_get_by_web_id_happy_path(self) -> None:
        respx.get(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(200, json=AR_PAYLOAD)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ar = _AsyncAR(client)
            result = await ar.get_by_web_id(AR_WID)
            assert isinstance(result, PIAnalysisRule)
            assert result.web_id == AR_WID
            assert result.plug_in_name == "PerformanceEquation"

    @respx.mock
    async def test_get_children_happy_path(self) -> None:
        respx.get(
            f"{BASE}/analysisrules/{AR_WID}/analysisrules"
        ).mock(return_value=httpx.Response(200, json=AR_LIST_PAYLOAD))
        async with httpx.AsyncClient(base_url=BASE) as client:
            ar = _AsyncAR(client)
            result = await ar.get_children(AR_WID)
            assert len(result) == 2

    @respx.mock
    async def test_create_child_happy_path(self) -> None:
        respx.post(
            f"{BASE}/analysisrules/{AR_WID}/analysisrules"
        ).mock(return_value=httpx.Response(201))
        async with httpx.AsyncClient(base_url=BASE) as client:
            ar = _AsyncAR(client)
            await ar.create_child(
                AR_WID, {"Name": "NewChild", "PlugInName": "PerformanceEquation"}
            )

    @respx.mock
    async def test_get_by_analysis_happy_path(self) -> None:
        respx.get(
            f"{BASE}/analyses/{AN_WID}/analysisrules"
        ).mock(return_value=httpx.Response(200, json=AR_LIST_PAYLOAD))
        async with httpx.AsyncClient(base_url=BASE) as client:
            ar = _AsyncAR(client)
            result = await ar.get_by_analysis(AN_WID)
            assert len(result) == 2

    @respx.mock
    async def test_create_on_analysis_happy_path(self) -> None:
        respx.post(
            f"{BASE}/analyses/{AN_WID}/analysisrules"
        ).mock(return_value=httpx.Response(201))
        async with httpx.AsyncClient(base_url=BASE) as client:
            ar = _AsyncAR(client)
            await ar.create_on_analysis(
                AN_WID, {"Name": "Root", "PlugInName": "PerformanceEquation"}
            )

    @respx.mock
    async def test_update_happy_path(self) -> None:
        respx.patch(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(204)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ar = _AsyncAR(client)
            await ar.update(AR_WID, {"ConfigString": "Out := 42;"})

    @respx.mock
    async def test_delete_happy_path(self) -> None:
        respx.delete(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(204)
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ar = _AsyncAR(client)
            await ar.delete(AR_WID)


class TestAnalysisRulesAsyncErrors:
    """Async error-path tests for AnalysisRules."""

    @respx.mock
    async def test_get_by_web_id_not_found(self) -> None:
        respx.get(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ar = _AsyncAR(client)
            with pytest.raises(NotFoundError):
                await ar.get_by_web_id(AR_WID)

    @respx.mock
    async def test_delete_server_error(self) -> None:
        respx.delete(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(
                500, json={"Errors": ["Internal error"]}
            )
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ar = _AsyncAR(client)
            with pytest.raises(ServerError):
                await ar.delete(AR_WID)

    @respx.mock
    async def test_update_not_found(self) -> None:
        respx.patch(f"{BASE}/analysisrules/{AR_WID}").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        async with httpx.AsyncClient(base_url=BASE) as client:
            ar = _AsyncAR(client)
            with pytest.raises(NotFoundError):
                await ar.update(AR_WID, {"ConfigString": "x"})
