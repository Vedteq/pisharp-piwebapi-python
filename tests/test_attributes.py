"""Tests for the standalone Attributes controller."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.attributes import AsyncAttributesMixin, AttributesMixin
from pisharp_piwebapi.exceptions import AuthenticationError, NotFoundError
from pisharp_piwebapi.models import PIAttribute, StreamValue

BASE = "https://piserver/piwebapi"
ATTR_WEB_ID = "AF0AttrXYZ"

ATTR_PAYLOAD = {
    "WebId": ATTR_WEB_ID,
    "Name": "Temperature",
    "Path": "\\\\AF\\DB\\Element|Temperature",
    "Description": "Process temperature",
    "Type": "Double",
    "TypeQualifier": "",
    "Value": None,
    "ConfigString": "\\\\PI\\sinusoid",
    "DataReferencePlugIn": "PI Point",
    "HasChildren": True,
    "IsConfigurationItem": False,
    "Links": {},
}

CHILD_ATTR = {
    "WebId": "AF0ChildHI",
    "Name": "High",
    "Path": "\\\\AF\\DB\\Element|Temperature|High",
    "Description": "High limit",
    "Type": "Double",
    "TypeQualifier": "",
    "Value": None,
    "ConfigString": "",
    "DataReferencePlugIn": "",
    "HasChildren": False,
    "IsConfigurationItem": True,
    "Links": {},
}

VALUE_PAYLOAD = {
    "Timestamp": "2024-06-15T12:00:00Z",
    "Value": 72.5,
    "UnitsAbbreviation": "degF",
    "Good": True,
    "Questionable": False,
    "Substituted": False,
    "Annotated": False,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _SyncAttrs(AttributesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncAttrs(AsyncAttributesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_by_web_id
# ===========================================================================


@respx.mock
def test_get_by_web_id() -> None:
    respx.get(f"{BASE}/attributes/{ATTR_WEB_ID}").mock(
        return_value=httpx.Response(200, json=ATTR_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        attr = _SyncAttrs(client).get_by_web_id(ATTR_WEB_ID)
    assert isinstance(attr, PIAttribute)
    assert attr.name == "Temperature"
    assert attr.has_children is True


@respx.mock
def test_get_by_web_id_not_found() -> None:
    respx.get(f"{BASE}/attributes/NOPE").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )
    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(NotFoundError):
            _SyncAttrs(client).get_by_web_id("NOPE")


# ===========================================================================
# Sync — get_by_path
# ===========================================================================


@respx.mock
def test_get_by_path() -> None:
    respx.get(f"{BASE}/attributes").mock(
        return_value=httpx.Response(200, json=ATTR_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        attr = _SyncAttrs(client).get_by_path("\\\\AF\\DB\\Element|Temperature")
    assert attr.web_id == ATTR_WEB_ID


# ===========================================================================
# Sync — get_value / set_value
# ===========================================================================


@respx.mock
def test_get_value() -> None:
    respx.get(f"{BASE}/attributes/{ATTR_WEB_ID}/value").mock(
        return_value=httpx.Response(200, json=VALUE_PAYLOAD)
    )
    with httpx.Client(base_url=BASE) as client:
        val = _SyncAttrs(client).get_value(ATTR_WEB_ID)
    assert isinstance(val, StreamValue)
    assert val.value == 72.5
    assert val.good is True


@respx.mock
def test_set_value() -> None:
    route = respx.put(f"{BASE}/attributes/{ATTR_WEB_ID}/value").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        _SyncAttrs(client).set_value(ATTR_WEB_ID, 100.0)
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["Value"] == 100.0
    assert "Timestamp" not in body


@respx.mock
def test_set_value_with_timestamp() -> None:
    route = respx.put(f"{BASE}/attributes/{ATTR_WEB_ID}/value").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        _SyncAttrs(client).set_value(
            ATTR_WEB_ID, 99.0, timestamp="2024-06-15T12:00:00Z"
        )
    body = json.loads(route.calls.last.request.content)
    assert body["Timestamp"] == "2024-06-15T12:00:00Z"


# ===========================================================================
# Sync — update
# ===========================================================================


@respx.mock
def test_update_attribute() -> None:
    route = respx.patch(f"{BASE}/attributes/{ATTR_WEB_ID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        _SyncAttrs(client).update(ATTR_WEB_ID, description="Updated")
    body = json.loads(route.calls.last.request.content)
    assert body == {"Description": "Updated"}


@respx.mock
def test_update_attribute_no_fields_is_noop() -> None:
    route = respx.patch(f"{BASE}/attributes/{ATTR_WEB_ID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        _SyncAttrs(client).update(ATTR_WEB_ID)
    assert not route.called


# ===========================================================================
# Sync — get_children
# ===========================================================================


@respx.mock
def test_get_children() -> None:
    respx.get(f"{BASE}/attributes/{ATTR_WEB_ID}/attributes").mock(
        return_value=httpx.Response(200, json={"Items": [CHILD_ATTR]})
    )
    with httpx.Client(base_url=BASE) as client:
        children = _SyncAttrs(client).get_children(ATTR_WEB_ID)
    assert len(children) == 1
    assert children[0].name == "High"
    assert children[0].is_configuration_item is True


# ===========================================================================
# Sync — delete
# ===========================================================================


@respx.mock
def test_delete_attribute() -> None:
    route = respx.delete(f"{BASE}/attributes/{ATTR_WEB_ID}").mock(
        return_value=httpx.Response(204)
    )
    with httpx.Client(base_url=BASE) as client:
        _SyncAttrs(client).delete(ATTR_WEB_ID)
    assert route.called


# ===========================================================================
# Async — get_by_web_id
# ===========================================================================


@respx.mock
async def test_async_get_by_web_id() -> None:
    respx.get(f"{BASE}/attributes/{ATTR_WEB_ID}").mock(
        return_value=httpx.Response(200, json=ATTR_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        attr = await _AsyncAttrs(client).get_by_web_id(ATTR_WEB_ID)
    assert attr.name == "Temperature"


# ===========================================================================
# Async — get_value / set_value
# ===========================================================================


@respx.mock
async def test_async_get_value() -> None:
    respx.get(f"{BASE}/attributes/{ATTR_WEB_ID}/value").mock(
        return_value=httpx.Response(200, json=VALUE_PAYLOAD)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        val = await _AsyncAttrs(client).get_value(ATTR_WEB_ID)
    assert val.value == 72.5


@respx.mock
async def test_async_set_value() -> None:
    route = respx.put(f"{BASE}/attributes/{ATTR_WEB_ID}/value").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        await _AsyncAttrs(client).set_value(ATTR_WEB_ID, 50.0)
    body = json.loads(route.calls.last.request.content)
    assert body["Value"] == 50.0


# ===========================================================================
# Async — get_children
# ===========================================================================


@respx.mock
async def test_async_get_children() -> None:
    respx.get(f"{BASE}/attributes/{ATTR_WEB_ID}/attributes").mock(
        return_value=httpx.Response(200, json={"Items": [CHILD_ATTR]})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        children = await _AsyncAttrs(client).get_children(ATTR_WEB_ID)
    assert len(children) == 1
    assert children[0].name == "High"


# ===========================================================================
# Async — delete
# ===========================================================================


@respx.mock
async def test_async_delete() -> None:
    route = respx.delete(f"{BASE}/attributes/{ATTR_WEB_ID}").mock(
        return_value=httpx.Response(204)
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        await _AsyncAttrs(client).delete(ATTR_WEB_ID)
    assert route.called


# ===========================================================================
# Async — 401 error
# ===========================================================================


@respx.mock
async def test_async_get_value_auth_error() -> None:
    respx.get(f"{BASE}/attributes/{ATTR_WEB_ID}/value").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )
    async with httpx.AsyncClient(base_url=BASE) as client:
        with pytest.raises(AuthenticationError):
            await _AsyncAttrs(client).get_value(ATTR_WEB_ID)
