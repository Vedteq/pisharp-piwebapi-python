"""Tests for AnalysisTemplates resource — sync and async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.analysistemplates import (
    AnalysisTemplatesMixin,
    AsyncAnalysisTemplatesMixin,
)
from pisharp_piwebapi.exceptions import NotFoundError, ServerError
from pisharp_piwebapi.models import PIAnalysisTemplate

BASE = "https://piserver/piwebapi"
AT_WID = "AT0flowcalc001"
ET_WID = "ET0pump001"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

AT_PAYLOAD = {
    "WebId": AT_WID,
    "Id": "guid-at-001",
    "Name": "FlowCalc",
    "Description": "Flow calculation template",
    "Path": "\\\\AF_SERVER\\DB\\ElementTemplates[Pump]\\AnalysisTemplates[FlowCalc]",
    "AnalysisRulePlugInName": "PerformanceEquation",
    "CategoryNames": ["Calculations"],
    "CreateEnabled": True,
    "GroupId": 0,
    "HasNotificationTemplate": False,
    "HasTarget": True,
    "OutputTime": "",
    "TargetName": "",
    "TimeRulePlugInName": "Periodic",
    "Links": {"Self": f"{BASE}/analysistemplates/{AT_WID}"},
}

AT_LIST_PAYLOAD = {
    "Items": [
        AT_PAYLOAD,
        {
            "WebId": "AT0efficiency001",
            "Id": "guid-at-002",
            "Name": "Efficiency",
            "Description": "Efficiency calculation",
            "Path": "",
            "AnalysisRulePlugInName": "PerformanceEquation",
            "CategoryNames": [],
            "CreateEnabled": False,
            "GroupId": 0,
            "HasNotificationTemplate": False,
            "HasTarget": False,
            "OutputTime": "",
            "TargetName": "",
            "TimeRulePlugInName": "",
            "Links": {},
        },
    ]
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SyncAT(AnalysisTemplatesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncAT(AsyncAnalysisTemplatesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_by_web_id
# ===========================================================================


@respx.mock
def test_get_by_web_id_happy_path() -> None:
    """get_by_web_id returns a PIAnalysisTemplate."""
    respx.get(f"{BASE}/analysistemplates/{AT_WID}").mock(
        return_value=httpx.Response(200, json=AT_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        result = at.get_by_web_id(AT_WID)
    assert isinstance(result, PIAnalysisTemplate)
    assert result.web_id == AT_WID
    assert result.name == "FlowCalc"
    assert result.analysis_rule_plugin_name == "PerformanceEquation"
    assert result.create_enabled is True


@respx.mock
def test_get_by_web_id_404_raises() -> None:
    """get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/analysistemplates/{AT_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        with pytest.raises(NotFoundError):
            at.get_by_web_id(AT_WID)


# ===========================================================================
# Sync — get_by_path
# ===========================================================================


@respx.mock
def test_get_by_path_happy_path() -> None:
    """get_by_path returns a PIAnalysisTemplate."""
    route = respx.get(f"{BASE}/analysistemplates").mock(
        return_value=httpx.Response(200, json=AT_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        result = at.get_by_path("\\\\AF\\DB\\ET[Pump]\\AT[FlowCalc]")
    assert isinstance(result, PIAnalysisTemplate)
    assert result.name == "FlowCalc"
    assert route.called
    assert b"path=" in route.calls.last.request.url.query


# ===========================================================================
# Sync — get_by_element_template
# ===========================================================================


@respx.mock
def test_get_by_element_template_happy_path() -> None:
    """get_by_element_template returns a list of PIAnalysisTemplate."""
    respx.get(
        f"{BASE}/elementtemplates/{ET_WID}/analysistemplates"
    ).mock(return_value=httpx.Response(200, json=AT_LIST_PAYLOAD))
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        results = at.get_by_element_template(ET_WID)
    assert len(results) == 2
    assert all(isinstance(r, PIAnalysisTemplate) for r in results)
    assert results[0].name == "FlowCalc"
    assert results[1].name == "Efficiency"


@respx.mock
def test_get_by_element_template_404_raises() -> None:
    """get_by_element_template raises NotFoundError on 404."""
    respx.get(
        f"{BASE}/elementtemplates/{ET_WID}/analysistemplates"
    ).mock(return_value=httpx.Response(404, json={"Message": "Not found"}))
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        with pytest.raises(NotFoundError):
            at.get_by_element_template(ET_WID)


@respx.mock
def test_get_by_element_template_empty() -> None:
    """get_by_element_template returns empty list for no items."""
    respx.get(
        f"{BASE}/elementtemplates/{ET_WID}/analysistemplates"
    ).mock(return_value=httpx.Response(200, json={"Items": []}))
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        results = at.get_by_element_template(ET_WID)
    assert results == []


# ===========================================================================
# Sync — update
# ===========================================================================


@respx.mock
def test_update_happy_path() -> None:
    """update sends PATCH request."""
    route = respx.patch(f"{BASE}/analysistemplates/{AT_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        at.update(AT_WID, {"Description": "updated"})
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["Description"] == "updated"


@respx.mock
def test_update_server_error_raises() -> None:
    """update raises ServerError on 500."""
    respx.patch(f"{BASE}/analysistemplates/{AT_WID}").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        with pytest.raises(ServerError):
            at.update(AT_WID, {"Description": "fail"})


# ===========================================================================
# Sync — delete
# ===========================================================================


@respx.mock
def test_delete_happy_path() -> None:
    """delete sends DELETE request."""
    route = respx.delete(f"{BASE}/analysistemplates/{AT_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        at.delete(AT_WID)
    assert route.called


@respx.mock
def test_delete_404_raises() -> None:
    """delete raises NotFoundError on 404."""
    respx.delete(f"{BASE}/analysistemplates/{AT_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        with pytest.raises(NotFoundError):
            at.delete(AT_WID)


# ===========================================================================
# Async — get_by_web_id
# ===========================================================================


@respx.mock
async def test_async_get_by_web_id_happy_path() -> None:
    """Async get_by_web_id returns a PIAnalysisTemplate."""
    respx.get(f"{BASE}/analysistemplates/{AT_WID}").mock(
        return_value=httpx.Response(200, json=AT_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        result = await at.get_by_web_id(AT_WID)
    assert isinstance(result, PIAnalysisTemplate)
    assert result.web_id == AT_WID


@respx.mock
async def test_async_get_by_web_id_404_raises() -> None:
    """Async get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/analysistemplates/{AT_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        with pytest.raises(NotFoundError):
            await at.get_by_web_id(AT_WID)


# ===========================================================================
# Async — get_by_path
# ===========================================================================


@respx.mock
async def test_async_get_by_path_happy_path() -> None:
    """Async get_by_path returns a PIAnalysisTemplate."""
    respx.get(f"{BASE}/analysistemplates").mock(
        return_value=httpx.Response(200, json=AT_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        result = await at.get_by_path("\\\\AF\\DB\\ET[Pump]\\AT[FlowCalc]")
    assert isinstance(result, PIAnalysisTemplate)
    assert result.name == "FlowCalc"


# ===========================================================================
# Async — get_by_element_template
# ===========================================================================


@respx.mock
async def test_async_get_by_element_template_happy_path() -> None:
    """Async get_by_element_template returns a list."""
    respx.get(
        f"{BASE}/elementtemplates/{ET_WID}/analysistemplates"
    ).mock(return_value=httpx.Response(200, json=AT_LIST_PAYLOAD))
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        results = await at.get_by_element_template(ET_WID)
    assert len(results) == 2
    assert results[0].name == "FlowCalc"


@respx.mock
async def test_async_get_by_element_template_404_raises() -> None:
    """Async get_by_element_template raises NotFoundError on 404."""
    respx.get(
        f"{BASE}/elementtemplates/{ET_WID}/analysistemplates"
    ).mock(return_value=httpx.Response(404, json={"Message": "Not found"}))
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        with pytest.raises(NotFoundError):
            await at.get_by_element_template(ET_WID)


# ===========================================================================
# Async — update / delete
# ===========================================================================


@respx.mock
async def test_async_update_happy_path() -> None:
    """Async update sends PATCH."""
    route = respx.patch(f"{BASE}/analysistemplates/{AT_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        await at.update(AT_WID, {"Description": "updated"})
    assert route.called


@respx.mock
async def test_async_delete_happy_path() -> None:
    """Async delete sends DELETE."""
    route = respx.delete(f"{BASE}/analysistemplates/{AT_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        await at.delete(AT_WID)
    assert route.called


@respx.mock
async def test_async_delete_server_error_raises() -> None:
    """Async delete raises ServerError on 500."""
    respx.delete(f"{BASE}/analysistemplates/{AT_WID}").mock(
        return_value=httpx.Response(500, json={"Message": "Server error"})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        with pytest.raises(ServerError):
            await at.delete(AT_WID)
