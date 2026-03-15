"""Tests for Points resource — sync and async."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import AuthenticationError, NotFoundError, ServerError
from pisharp_piwebapi.models import PIDataServer, PIPoint
from pisharp_piwebapi.points import AsyncPointsMixin, PointsMixin

BASE = "https://piserver/piwebapi"
DS_WEB_ID = "S0AbEDDataServer"

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

POINT_PAYLOAD = {
    "WebId": "P0ABC123",
    "Id": 42,
    "Name": "sinusoid",
    "Path": "\\\\SERVER\\sinusoid",
    "Descriptor": "12 Hour Sinusoid",
    "PointClass": "classic",
    "PointType": "Float32",
    "EngineeringUnits": "degC",
    "Future": False,
    "Links": {"Self": f"{BASE}/points/P0ABC123"},
}

SEARCH_PAYLOAD = {
    "Items": [POINT_PAYLOAD],
    "Links": {},
}


# ---------------------------------------------------------------------------
# Sync helpers
# ---------------------------------------------------------------------------


class _SyncPoints(PointsMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------


class _AsyncPoints(AsyncPointsMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_by_path
# ===========================================================================


@respx.mock
def test_get_by_path_happy_path() -> None:
    """get_by_path returns a populated PIPoint on 200."""
    respx.get(f"{BASE}/points").mock(return_value=httpx.Response(200, json=POINT_PAYLOAD))

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        point = pts.get_by_path(r"\\SERVER\sinusoid")

    assert isinstance(point, PIPoint)
    assert point.web_id == "P0ABC123"
    assert point.name == "sinusoid"
    assert point.point_type == "Float32"
    assert point.engineering_units == "degC"


@respx.mock
def test_get_by_path_not_found_raises() -> None:
    """get_by_path raises NotFoundError on 404."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(404, json={"Message": "Point not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        with pytest.raises(NotFoundError) as exc_info:
            pts.get_by_path(r"\\SERVER\missing")

    assert exc_info.value.status_code == 404
    assert "Point not found" in str(exc_info.value)


# ===========================================================================
# Sync — get_by_web_id
# ===========================================================================


@respx.mock
def test_get_by_web_id_happy_path() -> None:
    """get_by_web_id returns a populated PIPoint on 200."""
    respx.get(f"{BASE}/points/P0ABC123").mock(
        return_value=httpx.Response(200, json=POINT_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        point = pts.get_by_web_id("P0ABC123")

    assert point.web_id == "P0ABC123"


@respx.mock
def test_get_by_web_id_server_error_raises() -> None:
    """get_by_web_id raises ServerError on 500."""
    respx.get(f"{BASE}/points/BAD").mock(
        return_value=httpx.Response(500, json={"Message": "Internal error"})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        with pytest.raises(ServerError) as exc_info:
            pts.get_by_web_id("BAD")

    assert exc_info.value.status_code == 500


# ===========================================================================
# Sync — search
# ===========================================================================


@respx.mock
def test_search_returns_list() -> None:
    """search returns a list of PIPoint objects."""
    respx.get(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(200, json=SEARCH_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        results = pts.search(DS_WEB_ID, name_filter="sinu*")

    assert len(results) == 1
    assert results[0].name == "sinusoid"


@respx.mock
def test_search_passes_name_filter_param() -> None:
    """search sends nameFilter to the correct dataservers endpoint."""
    route = respx.get(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(200, json=SEARCH_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        pts.search(DS_WEB_ID, name_filter="sinu*", max_count=50)

    assert route.called
    request = route.calls.last.request
    assert b"nameFilter=sinu" in request.url.query
    assert b"maxCount=50" in request.url.query


@respx.mock
def test_search_plain_list_response() -> None:
    """search handles a bare list response (no Items wrapper)."""
    respx.get(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(200, json=[POINT_PAYLOAD])
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        results = pts.search(DS_WEB_ID)

    assert len(results) == 1


@respx.mock
def test_search_empty_result() -> None:
    """search returns an empty list when no points match."""
    respx.get(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(200, json={"Items": [], "Links": {}})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        results = pts.search(DS_WEB_ID, name_filter="nomatch*")

    assert results == []


@respx.mock
def test_search_not_found_raises() -> None:
    """search raises NotFoundError when the data server WebID is invalid."""
    respx.get(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(404, json={"Message": "Data server not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        with pytest.raises(NotFoundError):
            pts.search(DS_WEB_ID)


# ===========================================================================
# Async — get_by_path
# ===========================================================================


@respx.mock
async def test_async_get_by_path_happy_path() -> None:
    """Async get_by_path returns a populated PIPoint on 200."""
    respx.get(f"{BASE}/points").mock(return_value=httpx.Response(200, json=POINT_PAYLOAD))

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        point = await pts.get_by_path(r"\\SERVER\sinusoid")

    assert point.web_id == "P0ABC123"
    assert point.name == "sinusoid"


@respx.mock
async def test_async_get_by_path_not_found_raises() -> None:
    """Async get_by_path raises NotFoundError on 404."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        with pytest.raises(NotFoundError) as exc_info:
            await pts.get_by_path(r"\\SERVER\missing")

    assert exc_info.value.status_code == 404


# ===========================================================================
# Async — get_by_web_id
# ===========================================================================


@respx.mock
async def test_async_get_by_web_id_happy_path() -> None:
    """Async get_by_web_id returns a populated PIPoint on 200."""
    respx.get(f"{BASE}/points/P0ABC123").mock(
        return_value=httpx.Response(200, json=POINT_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        point = await pts.get_by_web_id("P0ABC123")

    assert point.web_id == "P0ABC123"


@respx.mock
async def test_async_get_by_web_id_auth_error_raises() -> None:
    """Async get_by_web_id raises AuthenticationError on 401."""
    respx.get(f"{BASE}/points/P0ABC123").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        with pytest.raises(AuthenticationError) as exc_info:
            await pts.get_by_web_id("P0ABC123")

    assert exc_info.value.status_code == 401


# ===========================================================================
# Async — search
# ===========================================================================


@respx.mock
async def test_async_search_returns_list() -> None:
    """Async search returns a list of PIPoint objects."""
    respx.get(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(200, json=SEARCH_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        results = await pts.search(DS_WEB_ID, name_filter="sinu*")

    assert len(results) == 1
    assert results[0].name == "sinusoid"


@respx.mock
async def test_async_search_not_found_raises() -> None:
    """Async search raises NotFoundError for an unknown data server."""
    respx.get(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(404, json={"Message": "Data server not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        with pytest.raises(NotFoundError):
            await pts.search(DS_WEB_ID)


# ---------------------------------------------------------------------------
# Shared data server payload
# ---------------------------------------------------------------------------

DATA_SERVER_PAYLOAD = {
    "WebId": DS_WEB_ID,
    "Name": "PIServer01",
    "Path": "\\\\PIServer01",
    "IsConnected": True,
    "ServerVersion": "3.4.400.1162",
    "Links": {"Self": f"{BASE}/dataservers/{DS_WEB_ID}"},
}

DATA_SERVERS_PAYLOAD = {"Items": [DATA_SERVER_PAYLOAD], "Links": {}}


# ===========================================================================
# Sync — get_data_servers
# ===========================================================================


@respx.mock
def test_get_data_servers_happy_path() -> None:
    """get_data_servers returns a list of PIDataServer objects."""
    respx.get(f"{BASE}/dataservers").mock(
        return_value=httpx.Response(200, json=DATA_SERVERS_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        servers = pts.get_data_servers()

    assert len(servers) == 1
    assert isinstance(servers[0], PIDataServer)
    assert servers[0].web_id == DS_WEB_ID
    assert servers[0].name == "PIServer01"
    assert servers[0].is_connected is True


@respx.mock
def test_get_data_servers_auth_error_raises() -> None:
    """get_data_servers raises AuthenticationError on 401."""
    respx.get(f"{BASE}/dataservers").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        with pytest.raises(AuthenticationError) as exc_info:
            pts.get_data_servers()

    assert exc_info.value.status_code == 401


# ===========================================================================
# Sync — get_data_server
# ===========================================================================


@respx.mock
def test_get_data_server_happy_path() -> None:
    """get_data_server returns a single PIDataServer by WebID."""
    respx.get(f"{BASE}/dataservers/{DS_WEB_ID}").mock(
        return_value=httpx.Response(200, json=DATA_SERVER_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        server = pts.get_data_server(DS_WEB_ID)

    assert isinstance(server, PIDataServer)
    assert server.web_id == DS_WEB_ID
    assert server.server_version == "3.4.400.1162"


@respx.mock
def test_get_data_server_not_found_raises() -> None:
    """get_data_server raises NotFoundError on 404."""
    respx.get(f"{BASE}/dataservers/{DS_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Data server not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        with pytest.raises(NotFoundError) as exc_info:
            pts.get_data_server(DS_WEB_ID)

    assert exc_info.value.status_code == 404


# ===========================================================================
# Async — get_data_servers
# ===========================================================================


@respx.mock
async def test_async_get_data_servers_happy_path() -> None:
    """Async get_data_servers returns a list of PIDataServer objects."""
    respx.get(f"{BASE}/dataservers").mock(
        return_value=httpx.Response(200, json=DATA_SERVERS_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        servers = await pts.get_data_servers()

    assert len(servers) == 1
    assert servers[0].name == "PIServer01"


@respx.mock
async def test_async_get_data_servers_auth_error_raises() -> None:
    """Async get_data_servers raises AuthenticationError on 401."""
    respx.get(f"{BASE}/dataservers").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        with pytest.raises(AuthenticationError):
            await pts.get_data_servers()


# ===========================================================================
# Async — get_data_server
# ===========================================================================


@respx.mock
async def test_async_get_data_server_happy_path() -> None:
    """Async get_data_server returns a single PIDataServer by WebID."""
    respx.get(f"{BASE}/dataservers/{DS_WEB_ID}").mock(
        return_value=httpx.Response(200, json=DATA_SERVER_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        server = await pts.get_data_server(DS_WEB_ID)

    assert server.web_id == DS_WEB_ID
    assert server.is_connected is True


@respx.mock
async def test_async_get_data_server_not_found_raises() -> None:
    """Async get_data_server raises NotFoundError on 404."""
    respx.get(f"{BASE}/dataservers/{DS_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        with pytest.raises(NotFoundError):
            await pts.get_data_server(DS_WEB_ID)


# ===========================================================================
# Sync — create_point
# ===========================================================================


@respx.mock
def test_create_point_happy_path() -> None:
    """create_point POSTs to /dataservers/{webId}/points and returns a PIPoint."""
    route = respx.post(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(201, json=POINT_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        point = pts.create_point(DS_WEB_ID, "sinusoid", engineering_units="degC")

    assert isinstance(point, PIPoint)
    assert point.name == "sinusoid"
    assert point.web_id == "P0ABC123"
    assert route.called


@respx.mock
def test_create_point_sends_correct_body() -> None:
    """create_point includes all standard fields in the JSON body."""
    route = respx.post(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(201, json=POINT_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        pts.create_point(
            DS_WEB_ID,
            "MyTag",
            point_type="Float64",
            point_class="classic",
            descriptor="A test tag",
            engineering_units="m/s",
            future=False,
        )

    body = json.loads(route.calls.last.request.content)
    assert body["Name"] == "MyTag"
    assert body["PointType"] == "Float64"
    assert body["Descriptor"] == "A test tag"
    assert body["EngineeringUnits"] == "m/s"
    assert body["Future"] is False


@respx.mock
def test_create_point_with_extra_fields() -> None:
    """create_point merges extra_fields into the request body."""
    route = respx.post(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(201, json=POINT_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        pts.create_point(DS_WEB_ID, "SomeTag", extra_fields={"Compressing": True})

    body = json.loads(route.calls.last.request.content)
    assert body["Compressing"] is True


@respx.mock
def test_create_point_auth_error_raises() -> None:
    """create_point raises AuthenticationError on 401."""
    respx.post(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        with pytest.raises(AuthenticationError) as exc_info:
            pts.create_point(DS_WEB_ID, "BadTag")

    assert exc_info.value.status_code == 401


@respx.mock
def test_create_point_conflict_raises() -> None:
    """create_point raises PIWebAPIError when the server returns 409 (tag exists)."""
    from pisharp_piwebapi.exceptions import PIWebAPIError

    respx.post(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(409, json={"Message": "Tag already exists"})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        with pytest.raises(PIWebAPIError) as exc_info:
            pts.create_point(DS_WEB_ID, "sinusoid")

    assert exc_info.value.status_code == 409
    assert "Tag already exists" in str(exc_info.value)


# ===========================================================================
# Sync — delete_point
# ===========================================================================


@respx.mock
def test_delete_point_happy_path() -> None:
    """delete_point issues DELETE and returns None on 204."""
    route = respx.delete(f"{BASE}/points/P0ABC123").mock(
        return_value=httpx.Response(204)
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        result = pts.delete_point("P0ABC123")

    assert result is None
    assert route.called


@respx.mock
def test_delete_point_not_found_raises() -> None:
    """delete_point raises NotFoundError on 404."""
    respx.delete(f"{BASE}/points/MISSING").mock(
        return_value=httpx.Response(404, json={"Message": "Point not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        with pytest.raises(NotFoundError) as exc_info:
            pts.delete_point("MISSING")

    assert exc_info.value.status_code == 404
    assert "Point not found" in str(exc_info.value)


@respx.mock
def test_delete_point_auth_error_raises() -> None:
    """delete_point raises AuthenticationError on 403."""
    respx.delete(f"{BASE}/points/P0ABC123").mock(
        return_value=httpx.Response(403, json={"Message": "Forbidden"})
    )

    with httpx.Client(base_url=BASE) as client:
        pts = _SyncPoints(client)
        with pytest.raises(AuthenticationError) as exc_info:
            pts.delete_point("P0ABC123")

    assert exc_info.value.status_code == 403


# ===========================================================================
# Async — create_point
# ===========================================================================


@respx.mock
async def test_async_create_point_happy_path() -> None:
    """Async create_point returns a PIPoint on 201."""
    respx.post(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(201, json=POINT_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        point = await pts.create_point(DS_WEB_ID, "sinusoid")

    assert isinstance(point, PIPoint)
    assert point.name == "sinusoid"


@respx.mock
async def test_async_create_point_sends_correct_body() -> None:
    """Async create_point sends the full body including all standard fields."""
    route = respx.post(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(201, json=POINT_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        await pts.create_point(
            DS_WEB_ID,
            "AsyncTag",
            point_type="Int32",
            engineering_units="rpm",
        )

    body = json.loads(route.calls.last.request.content)
    assert body["Name"] == "AsyncTag"
    assert body["PointType"] == "Int32"
    assert body["EngineeringUnits"] == "rpm"


@respx.mock
async def test_async_create_point_server_error_raises() -> None:
    """Async create_point raises ServerError on 500."""
    respx.post(f"{BASE}/dataservers/{DS_WEB_ID}/points").mock(
        return_value=httpx.Response(500, json={"Message": "Internal error"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        with pytest.raises(ServerError) as exc_info:
            await pts.create_point(DS_WEB_ID, "FailTag")

    assert exc_info.value.status_code == 500


# ===========================================================================
# Async — delete_point
# ===========================================================================


@respx.mock
async def test_async_delete_point_happy_path() -> None:
    """Async delete_point issues DELETE and returns None on 204."""
    route = respx.delete(f"{BASE}/points/P0ABC123").mock(
        return_value=httpx.Response(204)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        result = await pts.delete_point("P0ABC123")

    assert result is None
    assert route.called


@respx.mock
async def test_async_delete_point_not_found_raises() -> None:
    """Async delete_point raises NotFoundError on 404."""
    respx.delete(f"{BASE}/points/NOPE").mock(
        return_value=httpx.Response(404, json={"Message": "Point not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        pts = _AsyncPoints(client)
        with pytest.raises(NotFoundError) as exc_info:
            await pts.delete_point("NOPE")

    assert exc_info.value.status_code == 404
