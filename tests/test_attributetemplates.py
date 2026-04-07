"""Tests for AttributeTemplates standalone controller — sync and async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.attributetemplates import (
    AsyncAttributeTemplatesMixin,
    AttributeTemplatesMixin,
)
from pisharp_piwebapi.exceptions import NotFoundError, ServerError
from pisharp_piwebapi.models import PIAttributeTemplate, PICategory

BASE = "https://piserver/piwebapi"
AT_WID = "AT0temp001"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

AT_PAYLOAD = {
    "WebId": AT_WID,
    "Id": "guid-at-001",
    "Name": "Temperature",
    "Description": "Temperature attribute template",
    "Path": "\\\\AF\\DB\\ET[Pump]|AT[Temperature]",
    "Type": "Double",
    "TypeQualifier": "",
    "DefaultValue": None,
    "ConfigString": "",
    "DataReferencePlugIn": "PI Point",
    "HasChildren": False,
    "IsConfigurationItem": False,
    "IsExcluded": False,
    "IsHidden": False,
    "IsManualDataEntry": False,
    "CategoryNames": ["Process"],
    "TraitName": "",
    "DefaultUnitsName": "deg C",
    "Links": {"Self": f"{BASE}/attributetemplates/{AT_WID}"},
}

CHILD_AT_PAYLOAD = {
    "WebId": "AT0child001",
    "Id": "guid-at-child",
    "Name": "SubAttribute",
    "Description": "Child attribute template",
    "Path": "",
    "Type": "String",
    "Links": {},
}

CATEGORY_PAYLOAD = {
    "WebId": "CAT0proc001",
    "Id": "guid-cat-001",
    "Name": "Process",
    "Description": "Process category",
    "Path": "\\\\AF\\DB\\Categories[Process]",
    "Links": {},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SyncAT(AttributeTemplatesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncAT(AsyncAttributeTemplatesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_by_web_id
# ===========================================================================


@respx.mock
def test_get_by_web_id_happy_path() -> None:
    """get_by_web_id returns a PIAttributeTemplate."""
    respx.get(f"{BASE}/attributetemplates/{AT_WID}").mock(
        return_value=httpx.Response(200, json=AT_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        result = at.get_by_web_id(AT_WID)
    assert isinstance(result, PIAttributeTemplate)
    assert result.web_id == AT_WID
    assert result.name == "Temperature"
    assert result.data_reference_plugin == "PI Point"
    assert result.default_units_name == "deg C"
    assert result.category_names == ["Process"]


@respx.mock
def test_get_by_web_id_404_raises() -> None:
    """get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/attributetemplates/{AT_WID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        with pytest.raises(NotFoundError):
            at.get_by_web_id(AT_WID)


def test_get_by_web_id_invalid_web_id() -> None:
    """get_by_web_id raises ValueError for empty WebID."""
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        with pytest.raises(ValueError, match="web_id"):
            at.get_by_web_id("")


# ===========================================================================
# Sync — get_by_path
# ===========================================================================


@respx.mock
def test_get_by_path_happy_path() -> None:
    """get_by_path returns a PIAttributeTemplate."""
    route = respx.get(f"{BASE}/attributetemplates").mock(
        return_value=httpx.Response(200, json=AT_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        result = at.get_by_path("\\\\AF\\DB\\ET[Pump]|AT[Temperature]")
    assert isinstance(result, PIAttributeTemplate)
    assert result.name == "Temperature"
    assert route.called
    assert b"path=" in route.calls.last.request.url.query


# ===========================================================================
# Sync — get_attribute_templates (children)
# ===========================================================================


@respx.mock
def test_get_attribute_templates_happy_path() -> None:
    """get_attribute_templates returns a list of child templates."""
    respx.get(
        f"{BASE}/attributetemplates/{AT_WID}/attributetemplates"
    ).mock(
        return_value=httpx.Response(
            200, json={"Items": [CHILD_AT_PAYLOAD]}
        )
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        results = at.get_attribute_templates(AT_WID)
    assert len(results) == 1
    assert isinstance(results[0], PIAttributeTemplate)
    assert results[0].name == "SubAttribute"


@respx.mock
def test_get_attribute_templates_empty() -> None:
    """get_attribute_templates returns empty list when no children."""
    respx.get(
        f"{BASE}/attributetemplates/{AT_WID}/attributetemplates"
    ).mock(
        return_value=httpx.Response(200, json={"Items": []})
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        results = at.get_attribute_templates(AT_WID)
    assert results == []


@respx.mock
def test_get_attribute_templates_flat_array() -> None:
    """get_attribute_templates handles flat array response."""
    respx.get(
        f"{BASE}/attributetemplates/{AT_WID}/attributetemplates"
    ).mock(
        return_value=httpx.Response(200, json=[CHILD_AT_PAYLOAD])
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        results = at.get_attribute_templates(AT_WID)
    assert len(results) == 1


# ===========================================================================
# Sync — get_categories
# ===========================================================================


@respx.mock
def test_get_categories_happy_path() -> None:
    """get_categories returns a list of PICategory."""
    respx.get(
        f"{BASE}/attributetemplates/{AT_WID}/categories"
    ).mock(
        return_value=httpx.Response(
            200, json={"Items": [CATEGORY_PAYLOAD]}
        )
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        results = at.get_categories(AT_WID)
    assert len(results) == 1
    assert isinstance(results[0], PICategory)
    assert results[0].name == "Process"


@respx.mock
def test_get_categories_empty() -> None:
    """get_categories returns empty list when no categories."""
    respx.get(
        f"{BASE}/attributetemplates/{AT_WID}/categories"
    ).mock(
        return_value=httpx.Response(200, json={"Items": []})
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        results = at.get_categories(AT_WID)
    assert results == []


@respx.mock
def test_get_categories_404_raises() -> None:
    """get_categories raises NotFoundError on 404."""
    respx.get(
        f"{BASE}/attributetemplates/{AT_WID}/categories"
    ).mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        with pytest.raises(NotFoundError):
            at.get_categories(AT_WID)


# ===========================================================================
# Sync — update
# ===========================================================================


@respx.mock
def test_update_happy_path() -> None:
    """update sends PATCH request."""
    route = respx.patch(f"{BASE}/attributetemplates/{AT_WID}").mock(
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
    respx.patch(f"{BASE}/attributetemplates/{AT_WID}").mock(
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
    route = respx.delete(f"{BASE}/attributetemplates/{AT_WID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        at = _SyncAT(client)
        at.delete(AT_WID)
    assert route.called


@respx.mock
def test_delete_404_raises() -> None:
    """delete raises NotFoundError on 404."""
    respx.delete(f"{BASE}/attributetemplates/{AT_WID}").mock(
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
    """Async get_by_web_id returns a PIAttributeTemplate."""
    respx.get(f"{BASE}/attributetemplates/{AT_WID}").mock(
        return_value=httpx.Response(200, json=AT_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        result = await at.get_by_web_id(AT_WID)
    assert isinstance(result, PIAttributeTemplate)
    assert result.web_id == AT_WID


@respx.mock
async def test_async_get_by_web_id_404_raises() -> None:
    """Async get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/attributetemplates/{AT_WID}").mock(
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
    """Async get_by_path returns a PIAttributeTemplate."""
    respx.get(f"{BASE}/attributetemplates").mock(
        return_value=httpx.Response(200, json=AT_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        result = await at.get_by_path("\\\\AF\\DB\\ET[Pump]|AT[Temp]")
    assert isinstance(result, PIAttributeTemplate)
    assert result.name == "Temperature"


# ===========================================================================
# Async — get_attribute_templates (children)
# ===========================================================================


@respx.mock
async def test_async_get_attribute_templates_happy_path() -> None:
    """Async get_attribute_templates returns child list."""
    respx.get(
        f"{BASE}/attributetemplates/{AT_WID}/attributetemplates"
    ).mock(
        return_value=httpx.Response(
            200, json={"Items": [CHILD_AT_PAYLOAD]}
        )
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        results = await at.get_attribute_templates(AT_WID)
    assert len(results) == 1
    assert results[0].name == "SubAttribute"


# ===========================================================================
# Async — get_categories
# ===========================================================================


@respx.mock
async def test_async_get_categories_happy_path() -> None:
    """Async get_categories returns a list of PICategory."""
    respx.get(
        f"{BASE}/attributetemplates/{AT_WID}/categories"
    ).mock(
        return_value=httpx.Response(
            200, json={"Items": [CATEGORY_PAYLOAD]}
        )
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        results = await at.get_categories(AT_WID)
    assert len(results) == 1
    assert isinstance(results[0], PICategory)
    assert results[0].name == "Process"


@respx.mock
async def test_async_get_categories_404_raises() -> None:
    """Async get_categories raises NotFoundError on 404."""
    respx.get(
        f"{BASE}/attributetemplates/{AT_WID}/categories"
    ).mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        with pytest.raises(NotFoundError):
            await at.get_categories(AT_WID)


# ===========================================================================
# Async — update / delete
# ===========================================================================


@respx.mock
async def test_async_update_happy_path() -> None:
    """Async update sends PATCH."""
    route = respx.patch(f"{BASE}/attributetemplates/{AT_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        await at.update(AT_WID, {"Description": "updated"})
    assert route.called


@respx.mock
async def test_async_delete_happy_path() -> None:
    """Async delete sends DELETE."""
    route = respx.delete(f"{BASE}/attributetemplates/{AT_WID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        await at.delete(AT_WID)
    assert route.called


@respx.mock
async def test_async_delete_server_error_raises() -> None:
    """Async delete raises ServerError on 500."""
    respx.delete(f"{BASE}/attributetemplates/{AT_WID}").mock(
        return_value=httpx.Response(
            500, json={"Message": "Server error"}
        )
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        at = _AsyncAT(client)
        with pytest.raises(ServerError):
            await at.delete(AT_WID)
