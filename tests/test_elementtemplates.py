"""Tests for Element Templates resource — sync and async."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import AuthenticationError, NotFoundError
from pisharp_piwebapi.models import PIAttributeTemplate, PIElementTemplate
from pisharp_piwebapi.elementtemplates import (
    AsyncElementTemplatesMixin,
    ElementTemplatesMixin,
)

BASE = "https://piserver/piwebapi"
TMPL_WEB_ID = "E1AbETemplate123"
DB_WEB_ID = "E1AbEDatabase456"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

TEMPLATE_PAYLOAD = {
    "WebId": TMPL_WEB_ID,
    "Id": "abc-123",
    "Name": "BoilerTemplate",
    "Description": "Template for boiler elements",
    "Path": "\\\\AF_SERVER\\DB\\ElementTemplates[BoilerTemplate]",
    "InstanceType": "Element",
    "NamingPattern": "",
    "CategoryNames": ["Equipment"],
    "AllowElementToExtend": False,
    "BaseTemplate": "",
    "Severity": "None",
    "CanBeAcknowledged": False,
    "Links": {},
}

TEMPLATES_LIST_PAYLOAD = {
    "Items": [
        TEMPLATE_PAYLOAD,
        {
            "WebId": "E1AbETemplate789",
            "Name": "PumpTemplate",
            "Description": "Template for pump elements",
            "Path": "\\\\AF_SERVER\\DB\\ElementTemplates[PumpTemplate]",
            "InstanceType": "Element",
            "Links": {},
        },
    ]
}

ATTR_TEMPLATES_PAYLOAD = {
    "Items": [
        {
            "WebId": "E1AbEAttrTmpl001",
            "Name": "Temperature",
            "Type": "Double",
            "DefaultValue": 0.0,
            "DataReferencePlugIn": "PI Point",
            "HasChildren": False,
            "Links": {},
        },
        {
            "WebId": "E1AbEAttrTmpl002",
            "Name": "Pressure",
            "Type": "Double",
            "DefaultValue": 14.7,
            "DataReferencePlugIn": "PI Point",
            "HasChildren": False,
            "Links": {},
        },
    ]
}


# ---------------------------------------------------------------------------
# Sync / Async helpers
# ---------------------------------------------------------------------------


class _SyncTemplates(ElementTemplatesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncTemplates(AsyncElementTemplatesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_by_web_id
# ===========================================================================


@respx.mock
def test_get_by_web_id_happy_path() -> None:
    """get_by_web_id returns a PIElementTemplate."""
    respx.get(f"{BASE}/elementtemplates/{TMPL_WEB_ID}").mock(
        return_value=httpx.Response(200, json=TEMPLATE_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        tmpl = _SyncTemplates(client).get_by_web_id(TMPL_WEB_ID)

    assert isinstance(tmpl, PIElementTemplate)
    assert tmpl.web_id == TMPL_WEB_ID
    assert tmpl.name == "BoilerTemplate"
    assert tmpl.description == "Template for boiler elements"
    assert "Equipment" in tmpl.category_names


@respx.mock
def test_get_by_web_id_404_raises() -> None:
    """get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/elementtemplates/{TMPL_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(NotFoundError) as exc_info:
            _SyncTemplates(client).get_by_web_id(TMPL_WEB_ID)

    assert exc_info.value.status_code == 404


# ===========================================================================
# Sync — get_by_path
# ===========================================================================


@respx.mock
def test_get_by_path_happy_path() -> None:
    """get_by_path returns a PIElementTemplate."""
    respx.get(f"{BASE}/elementtemplates").mock(
        return_value=httpx.Response(200, json=TEMPLATE_PAYLOAD)
    )

    path = "\\\\AF_SERVER\\DB\\ElementTemplates[BoilerTemplate]"
    with httpx.Client(base_url=BASE) as client:
        tmpl = _SyncTemplates(client).get_by_path(path)

    assert isinstance(tmpl, PIElementTemplate)
    assert tmpl.name == "BoilerTemplate"


@respx.mock
def test_get_by_path_404_raises() -> None:
    """get_by_path raises NotFoundError on 404."""
    respx.get(f"{BASE}/elementtemplates").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(NotFoundError):
            _SyncTemplates(client).get_by_path("\\\\BAD\\PATH")


# ===========================================================================
# Sync — get_by_database
# ===========================================================================


@respx.mock
def test_get_by_database_happy_path() -> None:
    """get_by_database returns a list of PIElementTemplate."""
    respx.get(
        f"{BASE}/assetdatabases/{DB_WEB_ID}/elementtemplates"
    ).mock(return_value=httpx.Response(200, json=TEMPLATES_LIST_PAYLOAD))

    with httpx.Client(base_url=BASE) as client:
        templates = _SyncTemplates(client).get_by_database(DB_WEB_ID)

    assert len(templates) == 2
    assert all(isinstance(t, PIElementTemplate) for t in templates)
    assert templates[0].name == "BoilerTemplate"
    assert templates[1].name == "PumpTemplate"


@respx.mock
def test_get_by_database_passes_params() -> None:
    """get_by_database forwards nameFilter and maxCount."""
    route = respx.get(
        f"{BASE}/assetdatabases/{DB_WEB_ID}/elementtemplates"
    ).mock(return_value=httpx.Response(200, json=TEMPLATES_LIST_PAYLOAD))

    with httpx.Client(base_url=BASE) as client:
        _SyncTemplates(client).get_by_database(
            DB_WEB_ID, name_filter="Boiler*", max_count=50
        )

    request = route.calls.last.request
    assert b"nameFilter=Boiler" in request.url.query
    assert b"maxCount=50" in request.url.query


@respx.mock
def test_get_by_database_404_raises() -> None:
    """get_by_database raises NotFoundError on 404."""
    respx.get(
        f"{BASE}/assetdatabases/{DB_WEB_ID}/elementtemplates"
    ).mock(return_value=httpx.Response(404, json={"Message": "Not found"}))

    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(NotFoundError):
            _SyncTemplates(client).get_by_database(DB_WEB_ID)


# ===========================================================================
# Sync — get_attribute_templates
# ===========================================================================


@respx.mock
def test_get_attribute_templates_happy_path() -> None:
    """get_attribute_templates returns a list of PIAttributeTemplate."""
    respx.get(
        f"{BASE}/elementtemplates/{TMPL_WEB_ID}/attributetemplates"
    ).mock(return_value=httpx.Response(200, json=ATTR_TEMPLATES_PAYLOAD))

    with httpx.Client(base_url=BASE) as client:
        attrs = _SyncTemplates(client).get_attribute_templates(TMPL_WEB_ID)

    assert len(attrs) == 2
    assert all(isinstance(a, PIAttributeTemplate) for a in attrs)
    assert attrs[0].name == "Temperature"
    assert attrs[0].type == "Double"
    assert attrs[0].default_value == 0.0
    assert attrs[1].name == "Pressure"
    assert attrs[1].default_value == 14.7


@respx.mock
def test_get_attribute_templates_401_raises() -> None:
    """get_attribute_templates raises AuthenticationError on 401."""
    respx.get(
        f"{BASE}/elementtemplates/{TMPL_WEB_ID}/attributetemplates"
    ).mock(return_value=httpx.Response(401, json={"Message": "Unauthorized"}))

    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(AuthenticationError):
            _SyncTemplates(client).get_attribute_templates(TMPL_WEB_ID)


# ===========================================================================
# Async — get_by_web_id
# ===========================================================================


@respx.mock
async def test_async_get_by_web_id_happy_path() -> None:
    """Async get_by_web_id returns a PIElementTemplate."""
    respx.get(f"{BASE}/elementtemplates/{TMPL_WEB_ID}").mock(
        return_value=httpx.Response(200, json=TEMPLATE_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        tmpl = await _AsyncTemplates(client).get_by_web_id(TMPL_WEB_ID)

    assert isinstance(tmpl, PIElementTemplate)
    assert tmpl.name == "BoilerTemplate"


@respx.mock
async def test_async_get_by_web_id_404_raises() -> None:
    """Async get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/elementtemplates/{TMPL_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        with pytest.raises(NotFoundError):
            await _AsyncTemplates(client).get_by_web_id(TMPL_WEB_ID)


# ===========================================================================
# Async — get_by_path
# ===========================================================================


@respx.mock
async def test_async_get_by_path_happy_path() -> None:
    """Async get_by_path returns a PIElementTemplate."""
    respx.get(f"{BASE}/elementtemplates").mock(
        return_value=httpx.Response(200, json=TEMPLATE_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        tmpl = await _AsyncTemplates(client).get_by_path("\\\\AF\\DB\\T")

    assert isinstance(tmpl, PIElementTemplate)


# ===========================================================================
# Async — get_by_database
# ===========================================================================


@respx.mock
async def test_async_get_by_database_happy_path() -> None:
    """Async get_by_database returns a list of PIElementTemplate."""
    respx.get(
        f"{BASE}/assetdatabases/{DB_WEB_ID}/elementtemplates"
    ).mock(return_value=httpx.Response(200, json=TEMPLATES_LIST_PAYLOAD))

    async with httpx.AsyncClient(base_url=BASE) as client:
        templates = await _AsyncTemplates(client).get_by_database(
            DB_WEB_ID
        )

    assert len(templates) == 2


# ===========================================================================
# Async — get_attribute_templates
# ===========================================================================


@respx.mock
async def test_async_get_attribute_templates_happy_path() -> None:
    """Async get_attribute_templates returns a list of PIAttributeTemplate."""
    respx.get(
        f"{BASE}/elementtemplates/{TMPL_WEB_ID}/attributetemplates"
    ).mock(return_value=httpx.Response(200, json=ATTR_TEMPLATES_PAYLOAD))

    async with httpx.AsyncClient(base_url=BASE) as client:
        attrs = await _AsyncTemplates(client).get_attribute_templates(
            TMPL_WEB_ID
        )

    assert len(attrs) == 2
    assert all(isinstance(a, PIAttributeTemplate) for a in attrs)
    assert attrs[0].name == "Temperature"
