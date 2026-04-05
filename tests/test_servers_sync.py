"""Integration tests for AssetServers, DataServers, and Databases mixins (sync)."""

from __future__ import annotations

import httpx
import pytest
from conftest import (
    AF_DATABASE,
    ASSET_SERVER,
    DATA_SERVER,
    ELEMENT_PUMP,
)

from pisharp_piwebapi.exceptions import AuthenticationError, NotFoundError
from pisharp_piwebapi.models import (
    EnumerationSet,
    EventFrame,
    PIAssetServer,
    PIDatabase,
    PIDataServer,
    PIElement,
    PIElementTemplate,
    PITable,
)


class TestAssetServersSync:
    def test_list(self, sync_client):
        client, mock = sync_client
        mock.get("/assetservers").mock(
            return_value=httpx.Response(200, json={"Items": [ASSET_SERVER]})
        )
        servers = client.assetservers.list_all()
        assert len(servers) == 1
        assert isinstance(servers[0], PIAssetServer)
        assert servers[0].name == "MyAFServer"

    def test_get_by_web_id(self, sync_client):
        client, mock = sync_client
        mock.get("/assetservers/AS001").mock(return_value=httpx.Response(200, json=ASSET_SERVER))
        svr = client.assetservers.get_by_web_id("AS001")
        assert svr.is_connected is True
        assert svr.server_version == "2.10.9"

    def test_get_databases(self, sync_client):
        client, mock = sync_client
        mock.get("/assetservers/AS001/assetdatabases").mock(
            return_value=httpx.Response(200, json={"Items": [AF_DATABASE]})
        )
        dbs = client.assetservers.get_databases("AS001")
        assert len(dbs) == 1
        assert isinstance(dbs[0], PIDatabase)
        assert dbs[0].name == "Production"


class TestDataServersSync:
    def test_list(self, sync_client):
        client, mock = sync_client
        mock.get("/dataservers").mock(
            return_value=httpx.Response(200, json={"Items": [DATA_SERVER]})
        )
        servers = client.dataservers.list_all()
        assert len(servers) == 1
        assert isinstance(servers[0], PIDataServer)
        assert servers[0].name == "MyPIServer"

    def test_get_by_web_id(self, sync_client):
        client, mock = sync_client
        mock.get("/dataservers/DS001").mock(return_value=httpx.Response(200, json=DATA_SERVER))
        svr = client.dataservers.get_by_web_id("DS001")
        assert svr.is_connected is True


class TestDatabasesSync:
    def test_get_by_path(self, sync_client):
        client, mock = sync_client
        mock.get("/assetdatabases", params={"path": "\\\\MyAFServer\\Production"}).mock(
            return_value=httpx.Response(200, json=AF_DATABASE)
        )
        db = client.databases.get_by_path(r"\\MyAFServer\Production")
        assert isinstance(db, PIDatabase)
        assert db.name == "Production"

    def test_get_by_web_id(self, sync_client):
        client, mock = sync_client
        mock.get("/assetdatabases/DB001").mock(return_value=httpx.Response(200, json=AF_DATABASE))
        db = client.databases.get_by_web_id("DB001")
        assert db.web_id == "DB001"

    def test_get_elements(self, sync_client):
        client, mock = sync_client
        mock.get("/assetdatabases/DB001/elements").mock(
            return_value=httpx.Response(200, json={"Items": [ELEMENT_PUMP]})
        )
        elements = client.databases.get_elements("DB001")
        assert len(elements) == 1
        assert isinstance(elements[0], PIElement)
        assert elements[0].name == "Pump-001"


    def test_get_elementtemplates(self, sync_client):
        client, mock = sync_client
        tmpl = {
            "WebId": "ET001",
            "Name": "PumpTemplate",
            "Description": "Pump template",
            "Path": "\\\\AF\\Production\\ElementTemplates[PumpTemplate]",
            "InstanceType": "Element",
            "Links": {},
        }
        mock.get("/assetdatabases/DB001/elementtemplates").mock(
            return_value=httpx.Response(200, json={"Items": [tmpl]})
        )
        templates = client.databases.get_elementtemplates("DB001")
        assert len(templates) == 1
        assert isinstance(templates[0], PIElementTemplate)
        assert templates[0].name == "PumpTemplate"

    def test_get_enumerationsets(self, sync_client):
        client, mock = sync_client
        eset = {
            "WebId": "ES001",
            "Name": "StatusCodes",
            "Description": "Status codes",
            "Path": "\\\\AF\\Production\\EnumerationSets[StatusCodes]",
            "Links": {},
        }
        mock.get("/assetdatabases/DB001/enumerationsets").mock(
            return_value=httpx.Response(200, json={"Items": [eset]})
        )
        esets = client.databases.get_enumerationsets("DB001")
        assert len(esets) == 1
        assert isinstance(esets[0], EnumerationSet)
        assert esets[0].name == "StatusCodes"

    def test_get_eventframes(self, sync_client):
        client, mock = sync_client
        ef = {
            "WebId": "EF001",
            "Name": "Shutdown-001",
            "Description": "Planned shutdown",
            "StartTime": "2024-06-15T08:00:00Z",
            "EndTime": "2024-06-15T16:00:00Z",
            "Links": {},
        }
        mock.get("/assetdatabases/DB001/eventframes").mock(
            return_value=httpx.Response(200, json={"Items": [ef]})
        )
        frames = client.databases.get_eventframes("DB001")
        assert len(frames) == 1
        assert isinstance(frames[0], EventFrame)
        assert frames[0].name == "Shutdown-001"

    def test_get_tables(self, sync_client):
        client, mock = sync_client
        tbl = {
            "WebId": "TBL001",
            "Name": "LookupTable",
            "Description": "Lookup data",
            "Path": "\\\\AF\\Production\\Tables[LookupTable]",
            "Links": {},
        }
        mock.get("/assetdatabases/DB001/tables").mock(
            return_value=httpx.Response(200, json={"Items": [tbl]})
        )
        tables = client.databases.get_tables("DB001")
        assert len(tables) == 1
        assert isinstance(tables[0], PITable)
        assert tables[0].name == "LookupTable"

    def test_create_element_template(self, sync_client):
        client, mock = sync_client
        route = mock.post("/assetdatabases/DB001/elementtemplates").mock(
            return_value=httpx.Response(201)
        )
        client.databases.create_element_template(
            "DB001", "NewTemplate", description="A new template"
        )
        assert route.called

    def test_get_elementtemplates_404_raises(self, sync_client):
        client, mock = sync_client
        mock.get("/assetdatabases/MISSING/elementtemplates").mock(
            return_value=httpx.Response(
                404, json={"Message": "Database not found."}
            )
        )
        with pytest.raises(NotFoundError):
            client.databases.get_elementtemplates("MISSING")


class TestServersErrorPaths:
    """Verify servers/databases modules raise SDK exceptions, not raw httpx errors."""

    def test_asset_server_not_found(self, sync_client):
        client, mock = sync_client
        mock.get("/assetservers/MISSING").mock(
            return_value=httpx.Response(
                404, json={"Message": "Asset server not found."}
            )
        )
        with pytest.raises(NotFoundError):
            client.assetservers.get_by_web_id("MISSING")

    def test_data_server_unauthorized(self, sync_client):
        client, mock = sync_client
        mock.get("/dataservers").mock(
            return_value=httpx.Response(
                401, json={"Message": "Unauthorized."}
            )
        )
        with pytest.raises(AuthenticationError):
            client.dataservers.list_all()

    def test_database_not_found(self, sync_client):
        client, mock = sync_client
        mock.get("/assetdatabases/MISSING").mock(
            return_value=httpx.Response(
                404, json={"Message": "Database not found."}
            )
        )
        with pytest.raises(NotFoundError):
            client.databases.get_by_web_id("MISSING")
