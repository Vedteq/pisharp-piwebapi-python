"""Tests for AF Elements resource — sync and async."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.elements import AsyncElementsMixin, ElementsMixin
from pisharp_piwebapi.exceptions import AuthenticationError, NotFoundError, ServerError
from pisharp_piwebapi.models import PIAttribute, PIDatabase, PIElement

BASE = "https://piserver/piwebapi"
AS_WEB_ID = "A0AbEDAssetServer"
DB_WEB_ID = "D0AbEDDatabase"
EL_WEB_ID = "E0AbEDElement"
ATTR_WEB_ID = "AT0AbEDAttribute"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

DATABASE_PAYLOAD = {
    "WebId": DB_WEB_ID,
    "Name": "NuGreen",
    "Path": "\\\\AF_SERVER\\NuGreen",
    "Description": "NuGreen AF database",
    "Links": {"Self": f"{BASE}/assetdatabases/{DB_WEB_ID}"},
}

ELEMENT_PAYLOAD = {
    "WebId": EL_WEB_ID,
    "Name": "Reactor A",
    "Path": "\\\\AF_SERVER\\NuGreen\\Reactor A",
    "Description": "Primary reactor",
    "TemplateName": "Reactor",
    "HasChildren": True,
    "Links": {"Self": f"{BASE}/elements/{EL_WEB_ID}"},
}

ATTRIBUTE_PAYLOAD = {
    "WebId": ATTR_WEB_ID,
    "Name": "Temperature",
    "Path": "\\\\AF_SERVER\\NuGreen\\Reactor A|Temperature",
    "Description": "Reactor temperature",
    "Type": "Double",
    "Value": 98.6,
    "Links": {},
}

DATABASES_LIST = {"Items": [DATABASE_PAYLOAD], "Links": {}}
ELEMENTS_LIST = {"Items": [ELEMENT_PAYLOAD], "Links": {}}
ATTRIBUTES_LIST = {"Items": [ATTRIBUTE_PAYLOAD], "Links": {}}


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _SyncElements(ElementsMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncElements(AsyncElementsMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_databases
# ===========================================================================


@respx.mock
def test_get_databases_happy_path() -> None:
    """get_databases returns a list of PIDatabase objects for an asset server."""
    respx.get(f"{BASE}/assetservers/{AS_WEB_ID}/assetdatabases").mock(
        return_value=httpx.Response(200, json=DATABASES_LIST)
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        dbs = el.get_databases(AS_WEB_ID)

    assert len(dbs) == 1
    assert isinstance(dbs[0], PIDatabase)
    assert dbs[0].web_id == DB_WEB_ID
    assert dbs[0].name == "NuGreen"


@respx.mock
def test_get_databases_not_found_raises() -> None:
    """get_databases raises NotFoundError for an unknown asset server."""
    respx.get(f"{BASE}/assetservers/{AS_WEB_ID}/assetdatabases").mock(
        return_value=httpx.Response(404, json={"Message": "Asset server not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        with pytest.raises(NotFoundError) as exc_info:
            el.get_databases(AS_WEB_ID)

    assert exc_info.value.status_code == 404


# ===========================================================================
# Sync — get_database
# ===========================================================================


@respx.mock
def test_get_database_happy_path() -> None:
    """get_database returns a single PIDatabase by WebID."""
    respx.get(f"{BASE}/assetdatabases/{DB_WEB_ID}").mock(
        return_value=httpx.Response(200, json=DATABASE_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        db = el.get_database(DB_WEB_ID)

    assert isinstance(db, PIDatabase)
    assert db.web_id == DB_WEB_ID
    assert db.description == "NuGreen AF database"


@respx.mock
def test_get_database_server_error_raises() -> None:
    """get_database raises ServerError on 500."""
    respx.get(f"{BASE}/assetdatabases/{DB_WEB_ID}").mock(
        return_value=httpx.Response(500, json={"Message": "Internal error"})
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        with pytest.raises(ServerError) as exc_info:
            el.get_database(DB_WEB_ID)

    assert exc_info.value.status_code == 500


# ===========================================================================
# Sync — get_database_by_path
# ===========================================================================


@respx.mock
def test_get_database_by_path_happy_path() -> None:
    """get_database_by_path sends path as query param and returns PIDatabase."""
    route = respx.get(f"{BASE}/assetdatabases").mock(
        return_value=httpx.Response(200, json=DATABASE_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        db = el.get_database_by_path("\\\\AF_SERVER\\NuGreen")

    assert db.name == "NuGreen"
    assert b"path=" in route.calls.last.request.url.query


@respx.mock
def test_get_database_by_path_not_found_raises() -> None:
    """get_database_by_path raises NotFoundError on 404."""
    respx.get(f"{BASE}/assetdatabases").mock(
        return_value=httpx.Response(404, json={"Message": "Database not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        with pytest.raises(NotFoundError):
            el.get_database_by_path("\\\\AF_SERVER\\Missing")


# ===========================================================================
# Sync — get_elements
# ===========================================================================


@respx.mock
def test_get_elements_happy_path() -> None:
    """get_elements returns top-level PIElement objects in a database."""
    respx.get(f"{BASE}/assetdatabases/{DB_WEB_ID}/elements").mock(
        return_value=httpx.Response(200, json=ELEMENTS_LIST)
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        elements = el.get_elements(DB_WEB_ID)

    assert len(elements) == 1
    assert isinstance(elements[0], PIElement)
    assert elements[0].web_id == EL_WEB_ID
    assert elements[0].name == "Reactor A"
    assert elements[0].has_children is True


@respx.mock
def test_get_elements_passes_name_filter() -> None:
    """get_elements sends nameFilter and maxCount query params."""
    route = respx.get(f"{BASE}/assetdatabases/{DB_WEB_ID}/elements").mock(
        return_value=httpx.Response(200, json=ELEMENTS_LIST)
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        el.get_elements(DB_WEB_ID, name_filter="Reactor*", max_count=50)

    assert route.called
    query = route.calls.last.request.url.query
    assert b"nameFilter=Reactor" in query
    assert b"maxCount=50" in query


@respx.mock
def test_get_elements_empty_result() -> None:
    """get_elements returns an empty list when no elements match."""
    respx.get(f"{BASE}/assetdatabases/{DB_WEB_ID}/elements").mock(
        return_value=httpx.Response(200, json={"Items": [], "Links": {}})
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        elements = el.get_elements(DB_WEB_ID, name_filter="NoMatch*")

    assert elements == []


# ===========================================================================
# Sync — get_element
# ===========================================================================


@respx.mock
def test_get_element_happy_path() -> None:
    """get_element returns a single PIElement by WebID."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}").mock(
        return_value=httpx.Response(200, json=ELEMENT_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        element = el.get_element(EL_WEB_ID)

    assert isinstance(element, PIElement)
    assert element.template_name == "Reactor"


@respx.mock
def test_get_element_not_found_raises() -> None:
    """get_element raises NotFoundError on 404."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Element not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        with pytest.raises(NotFoundError) as exc_info:
            el.get_element(EL_WEB_ID)

    assert exc_info.value.status_code == 404


# ===========================================================================
# Sync — get_element_by_path
# ===========================================================================


@respx.mock
def test_get_element_by_path_happy_path() -> None:
    """get_element_by_path sends path as query param and returns PIElement."""
    route = respx.get(f"{BASE}/elements").mock(
        return_value=httpx.Response(200, json=ELEMENT_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        element = el.get_element_by_path("\\\\AF_SERVER\\NuGreen\\Reactor A")

    assert element.name == "Reactor A"
    assert b"path=" in route.calls.last.request.url.query


# ===========================================================================
# Sync — get_child_elements
# ===========================================================================


@respx.mock
def test_get_child_elements_happy_path() -> None:
    """get_child_elements returns direct children of a parent element."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}/elements").mock(
        return_value=httpx.Response(200, json=ELEMENTS_LIST)
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        children = el.get_child_elements(EL_WEB_ID)

    assert len(children) == 1
    assert children[0].web_id == EL_WEB_ID


@respx.mock
def test_get_child_elements_not_found_raises() -> None:
    """get_child_elements raises NotFoundError for unknown parent WebID."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}/elements").mock(
        return_value=httpx.Response(404, json={"Message": "Element not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        with pytest.raises(NotFoundError):
            el.get_child_elements(EL_WEB_ID)


# ===========================================================================
# Sync — get_attributes
# ===========================================================================


@respx.mock
def test_get_attributes_happy_path() -> None:
    """get_attributes returns a list of PIAttribute objects for an element."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}/attributes").mock(
        return_value=httpx.Response(200, json=ATTRIBUTES_LIST)
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        attrs = el.get_attributes(EL_WEB_ID)

    assert len(attrs) == 1
    assert isinstance(attrs[0], PIAttribute)
    assert attrs[0].name == "Temperature"
    assert attrs[0].type == "Double"


@respx.mock
def test_get_attributes_passes_name_filter() -> None:
    """get_attributes forwards nameFilter and maxCount query params."""
    route = respx.get(f"{BASE}/elements/{EL_WEB_ID}/attributes").mock(
        return_value=httpx.Response(200, json=ATTRIBUTES_LIST)
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        el.get_attributes(EL_WEB_ID, name_filter="Temp*", max_count=25)

    query = route.calls.last.request.url.query
    assert b"nameFilter=Temp" in query
    assert b"maxCount=25" in query


@respx.mock
def test_get_attributes_auth_error_raises() -> None:
    """get_attributes raises AuthenticationError on 403."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}/attributes").mock(
        return_value=httpx.Response(403, json={"Message": "Forbidden"})
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        with pytest.raises(AuthenticationError) as exc_info:
            el.get_attributes(EL_WEB_ID)

    assert exc_info.value.status_code == 403


# ===========================================================================
# Sync — get_attribute
# ===========================================================================


@respx.mock
def test_get_attribute_happy_path() -> None:
    """get_attribute returns a single PIAttribute by WebID."""
    respx.get(f"{BASE}/attributes/{ATTR_WEB_ID}").mock(
        return_value=httpx.Response(200, json=ATTRIBUTE_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        attr = el.get_attribute(ATTR_WEB_ID)

    assert isinstance(attr, PIAttribute)
    assert attr.web_id == ATTR_WEB_ID
    assert attr.value == 98.6


@respx.mock
def test_get_attribute_not_found_raises() -> None:
    """get_attribute raises NotFoundError on 404."""
    respx.get(f"{BASE}/attributes/{ATTR_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Attribute not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        el = _SyncElements(client)
        with pytest.raises(NotFoundError):
            el.get_attribute(ATTR_WEB_ID)


# ===========================================================================
# Async — get_databases
# ===========================================================================


@respx.mock
async def test_async_get_databases_happy_path() -> None:
    """Async get_databases returns a list of PIDatabase objects."""
    respx.get(f"{BASE}/assetservers/{AS_WEB_ID}/assetdatabases").mock(
        return_value=httpx.Response(200, json=DATABASES_LIST)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        dbs = await el.get_databases(AS_WEB_ID)

    assert len(dbs) == 1
    assert dbs[0].name == "NuGreen"


@respx.mock
async def test_async_get_databases_auth_error_raises() -> None:
    """Async get_databases raises AuthenticationError on 401."""
    respx.get(f"{BASE}/assetservers/{AS_WEB_ID}/assetdatabases").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        with pytest.raises(AuthenticationError):
            await el.get_databases(AS_WEB_ID)


# ===========================================================================
# Async — get_database
# ===========================================================================


@respx.mock
async def test_async_get_database_happy_path() -> None:
    """Async get_database returns a single PIDatabase by WebID."""
    respx.get(f"{BASE}/assetdatabases/{DB_WEB_ID}").mock(
        return_value=httpx.Response(200, json=DATABASE_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        db = await el.get_database(DB_WEB_ID)

    assert db.web_id == DB_WEB_ID


@respx.mock
async def test_async_get_database_not_found_raises() -> None:
    """Async get_database raises NotFoundError on 404."""
    respx.get(f"{BASE}/assetdatabases/{DB_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Database not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        with pytest.raises(NotFoundError):
            await el.get_database(DB_WEB_ID)


# ===========================================================================
# Async — get_database_by_path
# ===========================================================================


@respx.mock
async def test_async_get_database_by_path_happy_path() -> None:
    """Async get_database_by_path returns PIDatabase for a valid path."""
    respx.get(f"{BASE}/assetdatabases").mock(
        return_value=httpx.Response(200, json=DATABASE_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        db = await el.get_database_by_path("\\\\AF_SERVER\\NuGreen")

    assert db.name == "NuGreen"


# ===========================================================================
# Async — get_elements
# ===========================================================================


@respx.mock
async def test_async_get_elements_happy_path() -> None:
    """Async get_elements returns a list of PIElement objects."""
    respx.get(f"{BASE}/assetdatabases/{DB_WEB_ID}/elements").mock(
        return_value=httpx.Response(200, json=ELEMENTS_LIST)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        elements = await el.get_elements(DB_WEB_ID)

    assert len(elements) == 1
    assert elements[0].name == "Reactor A"


@respx.mock
async def test_async_get_elements_not_found_raises() -> None:
    """Async get_elements raises NotFoundError for unknown database WebID."""
    respx.get(f"{BASE}/assetdatabases/{DB_WEB_ID}/elements").mock(
        return_value=httpx.Response(404, json={"Message": "Database not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        with pytest.raises(NotFoundError):
            await el.get_elements(DB_WEB_ID)


# ===========================================================================
# Async — get_element
# ===========================================================================


@respx.mock
async def test_async_get_element_happy_path() -> None:
    """Async get_element returns a single PIElement by WebID."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}").mock(
        return_value=httpx.Response(200, json=ELEMENT_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        element = await el.get_element(EL_WEB_ID)

    assert element.has_children is True


@respx.mock
async def test_async_get_element_not_found_raises() -> None:
    """Async get_element raises NotFoundError on 404."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Element not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        with pytest.raises(NotFoundError):
            await el.get_element(EL_WEB_ID)


# ===========================================================================
# Async — get_element_by_path
# ===========================================================================


@respx.mock
async def test_async_get_element_by_path_happy_path() -> None:
    """Async get_element_by_path returns PIElement for a valid path."""
    respx.get(f"{BASE}/elements").mock(
        return_value=httpx.Response(200, json=ELEMENT_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        element = await el.get_element_by_path("\\\\AF_SERVER\\NuGreen\\Reactor A")

    assert element.name == "Reactor A"


# ===========================================================================
# Async — get_child_elements
# ===========================================================================


@respx.mock
async def test_async_get_child_elements_happy_path() -> None:
    """Async get_child_elements returns child PIElement objects."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}/elements").mock(
        return_value=httpx.Response(200, json=ELEMENTS_LIST)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        children = await el.get_child_elements(EL_WEB_ID)

    assert len(children) == 1


@respx.mock
async def test_async_get_child_elements_server_error_raises() -> None:
    """Async get_child_elements raises ServerError on 500."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}/elements").mock(
        return_value=httpx.Response(500, json={"Message": "Internal error"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        with pytest.raises(ServerError):
            await el.get_child_elements(EL_WEB_ID)


# ===========================================================================
# Async — get_attributes
# ===========================================================================


@respx.mock
async def test_async_get_attributes_happy_path() -> None:
    """Async get_attributes returns a list of PIAttribute objects."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}/attributes").mock(
        return_value=httpx.Response(200, json=ATTRIBUTES_LIST)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        attrs = await el.get_attributes(EL_WEB_ID)

    assert len(attrs) == 1
    assert attrs[0].name == "Temperature"


@respx.mock
async def test_async_get_attributes_not_found_raises() -> None:
    """Async get_attributes raises NotFoundError on 404."""
    respx.get(f"{BASE}/elements/{EL_WEB_ID}/attributes").mock(
        return_value=httpx.Response(404, json={"Message": "Element not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        with pytest.raises(NotFoundError):
            await el.get_attributes(EL_WEB_ID)


# ===========================================================================
# Async — get_attribute
# ===========================================================================


@respx.mock
async def test_async_get_attribute_happy_path() -> None:
    """Async get_attribute returns a single PIAttribute by WebID."""
    respx.get(f"{BASE}/attributes/{ATTR_WEB_ID}").mock(
        return_value=httpx.Response(200, json=ATTRIBUTE_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        attr = await el.get_attribute(ATTR_WEB_ID)

    assert attr.type == "Double"
    assert attr.value == 98.6


@respx.mock
async def test_async_get_attribute_auth_error_raises() -> None:
    """Async get_attribute raises AuthenticationError on 401."""
    respx.get(f"{BASE}/attributes/{ATTR_WEB_ID}").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        el = _AsyncElements(client)
        with pytest.raises(AuthenticationError):
            await el.get_attribute(ATTR_WEB_ID)
