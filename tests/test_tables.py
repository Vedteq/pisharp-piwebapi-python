"""Tests for Tables resource — sync and async."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import (
    AuthenticationError,
    NotFoundError,
    ServerError,
)
from pisharp_piwebapi.models import PITable, PITableData
from pisharp_piwebapi.tables import AsyncTablesMixin, TablesMixin

BASE = "https://piserver/piwebapi"
TABLE_WEB_ID = "E1AbETable001"

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

TABLE_PAYLOAD = {
    "WebId": TABLE_WEB_ID,
    "Id": "table-id-001",
    "Name": "LookupTable",
    "Description": "Material lookup data",
    "Path": "\\\\AF_SERVER\\DB\\Tables[LookupTable]",
    "CategoryNames": ["Reference"],
    "ConvertToLocalTime": False,
    "TimeZone": "",
    "Links": {"Self": f"{BASE}/tables/{TABLE_WEB_ID}"},
}

TABLE_DATA_PAYLOAD = {
    "Columns": {
        "MaterialCode": "String",
        "Density": "Double",
        "Unit": "String",
    },
    "Rows": [
        {"MaterialCode": "STEEL", "Density": 7850.0, "Unit": "kg/m3"},
        {"MaterialCode": "WATER", "Density": 997.0, "Unit": "kg/m3"},
    ],
}

TABLES_LIST_PAYLOAD = {
    "Items": [
        TABLE_PAYLOAD,
        {
            "WebId": "E1AbETable002",
            "Name": "ConfigTable",
            "Description": "System config",
            "Path": "\\\\AF_SERVER\\DB\\Tables[ConfigTable]",
            "CategoryNames": [],
            "Links": {},
        },
    ]
}


# ---------------------------------------------------------------------------
# Sync / Async helpers
# ---------------------------------------------------------------------------


class _SyncTables(TablesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncTables(AsyncTablesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ===========================================================================
# Sync — get_by_web_id
# ===========================================================================


@respx.mock
def test_get_by_web_id_happy_path() -> None:
    """get_by_web_id returns a PITable."""
    respx.get(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(200, json=TABLE_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        table = _SyncTables(client).get_by_web_id(TABLE_WEB_ID)

    assert isinstance(table, PITable)
    assert table.web_id == TABLE_WEB_ID
    assert table.name == "LookupTable"
    assert table.description == "Material lookup data"
    assert "Reference" in table.category_names


@respx.mock
def test_get_by_web_id_404_raises() -> None:
    """get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(NotFoundError) as exc_info:
            _SyncTables(client).get_by_web_id(TABLE_WEB_ID)

    assert exc_info.value.status_code == 404


def test_get_by_web_id_rejects_empty_web_id() -> None:
    """get_by_web_id raises ValueError for empty WebID."""
    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(ValueError, match="must not be empty"):
            _SyncTables(client).get_by_web_id("")


# ===========================================================================
# Sync — get_by_path
# ===========================================================================


@respx.mock
def test_get_by_path_happy_path() -> None:
    """get_by_path returns a PITable."""
    respx.get(f"{BASE}/tables").mock(
        return_value=httpx.Response(200, json=TABLE_PAYLOAD)
    )

    path = "\\\\AF_SERVER\\DB\\Tables[LookupTable]"
    with httpx.Client(base_url=BASE) as client:
        table = _SyncTables(client).get_by_path(path)

    assert isinstance(table, PITable)
    assert table.name == "LookupTable"


@respx.mock
def test_get_by_path_404_raises() -> None:
    """get_by_path raises NotFoundError on 404."""
    respx.get(f"{BASE}/tables").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(NotFoundError):
            _SyncTables(client).get_by_path("\\\\BAD\\PATH")


# ===========================================================================
# Sync — get_data
# ===========================================================================


@respx.mock
def test_get_data_happy_path() -> None:
    """get_data returns PITableData with columns and rows."""
    respx.get(f"{BASE}/tables/{TABLE_WEB_ID}/data").mock(
        return_value=httpx.Response(200, json=TABLE_DATA_PAYLOAD)
    )

    with httpx.Client(base_url=BASE) as client:
        data = _SyncTables(client).get_data(TABLE_WEB_ID)

    assert isinstance(data, PITableData)
    assert "MaterialCode" in data.columns
    assert data.columns["Density"] == "Double"
    assert len(data.rows) == 2
    assert data.rows[0]["MaterialCode"] == "STEEL"
    assert data.rows[1]["Density"] == 997.0


@respx.mock
def test_get_data_empty_table() -> None:
    """get_data handles empty table data."""
    respx.get(f"{BASE}/tables/{TABLE_WEB_ID}/data").mock(
        return_value=httpx.Response(
            200,
            json={"Columns": {"Col1": "String"}, "Rows": []},
        )
    )

    with httpx.Client(base_url=BASE) as client:
        data = _SyncTables(client).get_data(TABLE_WEB_ID)

    assert len(data.rows) == 0
    assert "Col1" in data.columns


@respx.mock
def test_get_data_404_raises() -> None:
    """get_data raises NotFoundError on 404."""
    respx.get(f"{BASE}/tables/{TABLE_WEB_ID}/data").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(NotFoundError):
            _SyncTables(client).get_data(TABLE_WEB_ID)


# ===========================================================================
# Sync — update_data
# ===========================================================================


@respx.mock
def test_update_data_happy_path() -> None:
    """update_data sends PUT with table data."""
    route = respx.put(f"{BASE}/tables/{TABLE_WEB_ID}/data").mock(
        return_value=httpx.Response(204)
    )

    with httpx.Client(base_url=BASE) as client:
        _SyncTables(client).update_data(TABLE_WEB_ID, TABLE_DATA_PAYLOAD)

    assert route.called


@respx.mock
def test_update_data_500_raises() -> None:
    """update_data raises ServerError on 500."""
    respx.put(f"{BASE}/tables/{TABLE_WEB_ID}/data").mock(
        return_value=httpx.Response(500, json={"Message": "Internal error"})
    )

    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(ServerError):
            _SyncTables(client).update_data(TABLE_WEB_ID, TABLE_DATA_PAYLOAD)


# ===========================================================================
# Sync — update
# ===========================================================================


@respx.mock
def test_update_happy_path() -> None:
    """update sends PATCH with provided fields."""
    route = respx.patch(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(204)
    )

    with httpx.Client(base_url=BASE) as client:
        _SyncTables(client).update(
            TABLE_WEB_ID, name="NewName", description="Updated"
        )

    assert route.called


@respx.mock
def test_update_no_fields_skips_request() -> None:
    """update does not send a request when no fields are provided."""
    route = respx.patch(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(204)
    )

    with httpx.Client(base_url=BASE) as client:
        _SyncTables(client).update(TABLE_WEB_ID)

    assert not route.called


@respx.mock
def test_update_401_raises() -> None:
    """update raises AuthenticationError on 401."""
    respx.patch(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(AuthenticationError):
            _SyncTables(client).update(TABLE_WEB_ID, name="X")


# ===========================================================================
# Sync — delete
# ===========================================================================


@respx.mock
def test_delete_happy_path() -> None:
    """delete sends DELETE request."""
    route = respx.delete(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(204)
    )

    with httpx.Client(base_url=BASE) as client:
        _SyncTables(client).delete(TABLE_WEB_ID)

    assert route.called


@respx.mock
def test_delete_404_raises() -> None:
    """delete raises NotFoundError on 404."""
    respx.delete(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    with httpx.Client(base_url=BASE) as client:
        with pytest.raises(NotFoundError):
            _SyncTables(client).delete(TABLE_WEB_ID)


# ===========================================================================
# Async — get_by_web_id
# ===========================================================================


@respx.mock
async def test_async_get_by_web_id_happy_path() -> None:
    """Async get_by_web_id returns a PITable."""
    respx.get(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(200, json=TABLE_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        table = await _AsyncTables(client).get_by_web_id(TABLE_WEB_ID)

    assert isinstance(table, PITable)
    assert table.name == "LookupTable"


@respx.mock
async def test_async_get_by_web_id_404_raises() -> None:
    """Async get_by_web_id raises NotFoundError on 404."""
    respx.get(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        with pytest.raises(NotFoundError):
            await _AsyncTables(client).get_by_web_id(TABLE_WEB_ID)


# ===========================================================================
# Async — get_by_path
# ===========================================================================


@respx.mock
async def test_async_get_by_path_happy_path() -> None:
    """Async get_by_path returns a PITable."""
    respx.get(f"{BASE}/tables").mock(
        return_value=httpx.Response(200, json=TABLE_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        table = await _AsyncTables(client).get_by_path("\\\\AF\\DB\\T")

    assert isinstance(table, PITable)


# ===========================================================================
# Async — get_data
# ===========================================================================


@respx.mock
async def test_async_get_data_happy_path() -> None:
    """Async get_data returns PITableData."""
    respx.get(f"{BASE}/tables/{TABLE_WEB_ID}/data").mock(
        return_value=httpx.Response(200, json=TABLE_DATA_PAYLOAD)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        data = await _AsyncTables(client).get_data(TABLE_WEB_ID)

    assert isinstance(data, PITableData)
    assert len(data.rows) == 2


# ===========================================================================
# Async — update_data
# ===========================================================================


@respx.mock
async def test_async_update_data_happy_path() -> None:
    """Async update_data sends PUT."""
    route = respx.put(f"{BASE}/tables/{TABLE_WEB_ID}/data").mock(
        return_value=httpx.Response(204)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        await _AsyncTables(client).update_data(
            TABLE_WEB_ID, TABLE_DATA_PAYLOAD
        )

    assert route.called


# ===========================================================================
# Async — update
# ===========================================================================


@respx.mock
async def test_async_update_happy_path() -> None:
    """Async update sends PATCH."""
    route = respx.patch(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(204)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        await _AsyncTables(client).update(TABLE_WEB_ID, name="NewName")

    assert route.called


# ===========================================================================
# Async — delete
# ===========================================================================


@respx.mock
async def test_async_delete_happy_path() -> None:
    """Async delete sends DELETE."""
    route = respx.delete(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(204)
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        await _AsyncTables(client).delete(TABLE_WEB_ID)

    assert route.called


@respx.mock
async def test_async_delete_404_raises() -> None:
    """Async delete raises NotFoundError on 404."""
    respx.delete(f"{BASE}/tables/{TABLE_WEB_ID}").mock(
        return_value=httpx.Response(404, json={"Message": "Not found"})
    )

    async with httpx.AsyncClient(base_url=BASE) as client:
        with pytest.raises(NotFoundError):
            await _AsyncTables(client).delete(TABLE_WEB_ID)
