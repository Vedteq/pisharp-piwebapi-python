"""Integration tests for AssetServers, DataServers, and Databases mixins (async)."""

from __future__ import annotations

import httpx
from conftest import (
    AF_DATABASE,
    ASSET_SERVER,
    DATA_SERVER,
    ELEMENT_PUMP,
)

from pisharp_piwebapi.models import PIAssetServer, PIDatabase, PIDataServer, PIElement


class TestAssetServersAsync:
    async def test_list(self, async_client):
        client, mock = async_client
        mock.get("/assetservers").mock(
            return_value=httpx.Response(200, json={"Items": [ASSET_SERVER]})
        )
        servers = await client.assetservers.list_all()
        assert len(servers) == 1
        assert isinstance(servers[0], PIAssetServer)

    async def test_get_by_web_id(self, async_client):
        client, mock = async_client
        mock.get("/assetservers/AS001").mock(return_value=httpx.Response(200, json=ASSET_SERVER))
        svr = await client.assetservers.get_by_web_id("AS001")
        assert svr.is_connected is True

    async def test_get_databases(self, async_client):
        client, mock = async_client
        mock.get("/assetservers/AS001/assetdatabases").mock(
            return_value=httpx.Response(200, json={"Items": [AF_DATABASE]})
        )
        dbs = await client.assetservers.get_databases("AS001")
        assert len(dbs) == 1
        assert isinstance(dbs[0], PIDatabase)


class TestDataServersAsync:
    async def test_list(self, async_client):
        client, mock = async_client
        mock.get("/dataservers").mock(
            return_value=httpx.Response(200, json={"Items": [DATA_SERVER]})
        )
        servers = await client.dataservers.list_all()
        assert len(servers) == 1
        assert isinstance(servers[0], PIDataServer)

    async def test_get_by_web_id(self, async_client):
        client, mock = async_client
        mock.get("/dataservers/DS001").mock(return_value=httpx.Response(200, json=DATA_SERVER))
        svr = await client.dataservers.get_by_web_id("DS001")
        assert svr.is_connected is True


class TestDatabasesAsync:
    async def test_get_by_path(self, async_client):
        client, mock = async_client
        mock.get("/assetdatabases", params={"path": "\\\\MyAFServer\\Production"}).mock(
            return_value=httpx.Response(200, json=AF_DATABASE)
        )
        db = await client.databases.get_by_path(r"\\MyAFServer\Production")
        assert isinstance(db, PIDatabase)

    async def test_get_by_web_id(self, async_client):
        client, mock = async_client
        mock.get("/assetdatabases/DB001").mock(return_value=httpx.Response(200, json=AF_DATABASE))
        db = await client.databases.get_by_web_id("DB001")
        assert db.web_id == "DB001"

    async def test_get_elements(self, async_client):
        client, mock = async_client
        mock.get("/assetdatabases/DB001/elements").mock(
            return_value=httpx.Response(200, json={"Items": [ELEMENT_PUMP]})
        )
        elements = await client.databases.get_elements("DB001")
        assert len(elements) == 1
        assert isinstance(elements[0], PIElement)
