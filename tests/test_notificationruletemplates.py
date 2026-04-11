"""Tests for NotificationRuleTemplates resource — sync and async."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.exceptions import NotFoundError, ServerError
from pisharp_piwebapi.models import (
    PINotificationRuleSubscriber,
    PINotificationRuleTemplate,
)
from pisharp_piwebapi.notificationruletemplates import (
    AsyncNotificationRuleTemplatesMixin,
    NotificationRuleTemplatesMixin,
)

BASE = "https://piserver/piwebapi"
NRT_WID = "N1TPumpOverheat001"
DB_WID = "D0production001"

NRT_PAYLOAD = {
    "WebId": NRT_WID,
    "Id": "guid-nrt-001",
    "Name": "PumpOverheat",
    "Description": "Alert when pump temperature exceeds threshold",
    "Path": "\\\\AF_SERVER\\Prod\\NotificationRuleTemplates[PumpOverheat]",
    "AutoCreated": False,
    "CategoryNames": ["Critical"],
    "Criteria": "'Temperature' > 200",
    "MultiTriggerEventOption": "UseEachTrigger",
    "NonrepetitionInterval": "1h",
    "ResendInterval": "30m",
    "Status": "Enabled",
    "TargetName": "PumpTemplate",
    "Links": {"Self": f"{BASE}/notificationruletemplates/{NRT_WID}"},
}

NRT_LIST_PAYLOAD = {"Items": [NRT_PAYLOAD]}

SUBSCRIBER_PAYLOAD = {
    "WebId": "S1sub001",
    "Id": "guid-sub-001",
    "Name": "OpsEmail",
    "Description": "",
    "Path": f"{NRT_PAYLOAD['Path']}|Subscribers\\OpsEmail",
    "ConfigString": "",
    "ContactTemplateName": "OpsTeam",
    "ContactType": "Email",
    "DeliveryChannelName": "Email",
    "PlugInName": "Email",
    "EscalationTimeout": "",
    "IsEnabled": True,
    "Links": {},
}


class _SyncNRT(NotificationRuleTemplatesMixin):
    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncNRT(AsyncNotificationRuleTemplatesMixin):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


# ========================== SYNC TESTS ==========================


class TestNotificationRuleTemplatesSync:
    """Sync happy-path tests."""

    @respx.mock
    def test_get_by_web_id_happy_path(self) -> None:
        respx.get(f"{BASE}/notificationruletemplates/{NRT_WID}").mock(
            return_value=httpx.Response(200, json=NRT_PAYLOAD)
        )
        client = httpx.Client(base_url=BASE)
        nrt = _SyncNRT(client)
        result = nrt.get_by_web_id(NRT_WID)
        assert isinstance(result, PINotificationRuleTemplate)
        assert result.web_id == NRT_WID
        assert result.name == "PumpOverheat"
        assert result.criteria == "'Temperature' > 200"
        assert result.target_name == "PumpTemplate"
        client.close()

    @respx.mock
    def test_get_by_web_id_selected_fields(self) -> None:
        route = respx.get(
            f"{BASE}/notificationruletemplates/{NRT_WID}",
            params={"selectedFields": "WebId;Name"},
        ).mock(return_value=httpx.Response(200, json=NRT_PAYLOAD))
        client = httpx.Client(base_url=BASE)
        _SyncNRT(client).get_by_web_id(NRT_WID, selected_fields="WebId;Name")
        assert route.called
        client.close()

    @respx.mock
    def test_get_by_path_happy_path(self) -> None:
        path = NRT_PAYLOAD["Path"]
        route = respx.get(
            f"{BASE}/notificationruletemplates", params={"path": path}
        ).mock(return_value=httpx.Response(200, json=NRT_PAYLOAD))
        client = httpx.Client(base_url=BASE)
        result = _SyncNRT(client).get_by_path(path)
        assert route.called
        assert result.name == "PumpOverheat"
        client.close()

    @respx.mock
    def test_get_by_database_happy_path(self) -> None:
        respx.get(
            f"{BASE}/assetdatabases/{DB_WID}/notificationruletemplates",
            params={"nameFilter": "*", "maxCount": 100},
        ).mock(return_value=httpx.Response(200, json=NRT_LIST_PAYLOAD))
        client = httpx.Client(base_url=BASE)
        result = _SyncNRT(client).get_by_database(DB_WID)
        assert len(result) == 1
        assert result[0].name == "PumpOverheat"
        client.close()

    @respx.mock
    def test_get_by_database_empty(self) -> None:
        respx.get(
            f"{BASE}/assetdatabases/{DB_WID}/notificationruletemplates",
            params={"nameFilter": "*", "maxCount": 100},
        ).mock(return_value=httpx.Response(200, json={}))
        client = httpx.Client(base_url=BASE)
        result = _SyncNRT(client).get_by_database(DB_WID)
        assert result == []
        client.close()

    @respx.mock
    def test_create_on_database_happy_path(self) -> None:
        route = respx.post(
            f"{BASE}/assetdatabases/{DB_WID}/notificationruletemplates"
        ).mock(return_value=httpx.Response(201))
        client = httpx.Client(base_url=BASE)
        _SyncNRT(client).create_on_database(
            DB_WID, {"Name": "PumpOverheat", "Criteria": "'Temp' > 200"}
        )
        assert route.called
        client.close()

    @respx.mock
    def test_get_subscribers_happy_path(self) -> None:
        respx.get(
            f"{BASE}/notificationruletemplates/{NRT_WID}"
            "/notificationrulesubscribers"
        ).mock(
            return_value=httpx.Response(200, json={"Items": [SUBSCRIBER_PAYLOAD]})
        )
        client = httpx.Client(base_url=BASE)
        result = _SyncNRT(client).get_subscribers(NRT_WID)
        assert len(result) == 1
        assert isinstance(result[0], PINotificationRuleSubscriber)
        assert result[0].name == "OpsEmail"
        client.close()

    @respx.mock
    def test_update_happy_path(self) -> None:
        route = respx.patch(f"{BASE}/notificationruletemplates/{NRT_WID}").mock(
            return_value=httpx.Response(204)
        )
        client = httpx.Client(base_url=BASE)
        _SyncNRT(client).update(NRT_WID, {"ResendInterval": "1h"})
        assert route.called
        client.close()

    @respx.mock
    def test_delete_happy_path(self) -> None:
        route = respx.delete(f"{BASE}/notificationruletemplates/{NRT_WID}").mock(
            return_value=httpx.Response(204)
        )
        client = httpx.Client(base_url=BASE)
        _SyncNRT(client).delete(NRT_WID)
        assert route.called
        client.close()


class TestNotificationRuleTemplatesSyncErrors:
    """Sync error-path tests."""

    @respx.mock
    def test_get_by_web_id_not_found(self) -> None:
        respx.get(f"{BASE}/notificationruletemplates/{NRT_WID}").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Template not found"]}
            )
        )
        client = httpx.Client(base_url=BASE)
        with pytest.raises(NotFoundError):
            _SyncNRT(client).get_by_web_id(NRT_WID)
        client.close()

    @respx.mock
    def test_create_on_database_server_error(self) -> None:
        respx.post(
            f"{BASE}/assetdatabases/{DB_WID}/notificationruletemplates"
        ).mock(return_value=httpx.Response(500, json={"Errors": ["boom"]}))
        client = httpx.Client(base_url=BASE)
        with pytest.raises(ServerError):
            _SyncNRT(client).create_on_database(DB_WID, {"Name": "x"})
        client.close()

    def test_get_by_web_id_empty_web_id_raises(self) -> None:
        client = httpx.Client(base_url=BASE)
        with pytest.raises(ValueError):
            _SyncNRT(client).get_by_web_id("")
        client.close()

    def test_get_by_database_empty_web_id_raises(self) -> None:
        client = httpx.Client(base_url=BASE)
        with pytest.raises(ValueError):
            _SyncNRT(client).get_by_database("")
        client.close()


# ========================== ASYNC TESTS ==========================


class TestNotificationRuleTemplatesAsync:
    """Async happy-path tests."""

    @respx.mock
    async def test_get_by_web_id_happy_path(self) -> None:
        respx.get(f"{BASE}/notificationruletemplates/{NRT_WID}").mock(
            return_value=httpx.Response(200, json=NRT_PAYLOAD)
        )
        client = httpx.AsyncClient(base_url=BASE)
        result = await _AsyncNRT(client).get_by_web_id(NRT_WID)
        assert result.name == "PumpOverheat"
        await client.aclose()

    @respx.mock
    async def test_get_by_path_happy_path(self) -> None:
        path = NRT_PAYLOAD["Path"]
        respx.get(
            f"{BASE}/notificationruletemplates", params={"path": path}
        ).mock(return_value=httpx.Response(200, json=NRT_PAYLOAD))
        client = httpx.AsyncClient(base_url=BASE)
        result = await _AsyncNRT(client).get_by_path(path)
        assert result.web_id == NRT_WID
        await client.aclose()

    @respx.mock
    async def test_get_by_database_happy_path(self) -> None:
        respx.get(
            f"{BASE}/assetdatabases/{DB_WID}/notificationruletemplates",
            params={"nameFilter": "*", "maxCount": 100},
        ).mock(return_value=httpx.Response(200, json=NRT_LIST_PAYLOAD))
        client = httpx.AsyncClient(base_url=BASE)
        result = await _AsyncNRT(client).get_by_database(DB_WID)
        assert len(result) == 1
        await client.aclose()

    @respx.mock
    async def test_create_on_database_happy_path(self) -> None:
        route = respx.post(
            f"{BASE}/assetdatabases/{DB_WID}/notificationruletemplates"
        ).mock(return_value=httpx.Response(201))
        client = httpx.AsyncClient(base_url=BASE)
        await _AsyncNRT(client).create_on_database(DB_WID, {"Name": "x"})
        assert route.called
        await client.aclose()

    @respx.mock
    async def test_get_subscribers_happy_path(self) -> None:
        respx.get(
            f"{BASE}/notificationruletemplates/{NRT_WID}"
            "/notificationrulesubscribers"
        ).mock(
            return_value=httpx.Response(200, json={"Items": [SUBSCRIBER_PAYLOAD]})
        )
        client = httpx.AsyncClient(base_url=BASE)
        result = await _AsyncNRT(client).get_subscribers(NRT_WID)
        assert len(result) == 1
        await client.aclose()

    @respx.mock
    async def test_update_happy_path(self) -> None:
        route = respx.patch(f"{BASE}/notificationruletemplates/{NRT_WID}").mock(
            return_value=httpx.Response(204)
        )
        client = httpx.AsyncClient(base_url=BASE)
        await _AsyncNRT(client).update(NRT_WID, {"ResendInterval": "2h"})
        assert route.called
        await client.aclose()

    @respx.mock
    async def test_delete_happy_path(self) -> None:
        route = respx.delete(
            f"{BASE}/notificationruletemplates/{NRT_WID}"
        ).mock(return_value=httpx.Response(204))
        client = httpx.AsyncClient(base_url=BASE)
        await _AsyncNRT(client).delete(NRT_WID)
        assert route.called
        await client.aclose()


class TestNotificationRuleTemplatesAsyncErrors:
    """Async error-path tests."""

    @respx.mock
    async def test_get_by_web_id_not_found(self) -> None:
        respx.get(f"{BASE}/notificationruletemplates/{NRT_WID}").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Template not found"]}
            )
        )
        client = httpx.AsyncClient(base_url=BASE)
        with pytest.raises(NotFoundError):
            await _AsyncNRT(client).get_by_web_id(NRT_WID)
        await client.aclose()

    async def test_get_by_web_id_empty_web_id_raises(self) -> None:
        client = httpx.AsyncClient(base_url=BASE)
        with pytest.raises(ValueError):
            await _AsyncNRT(client).get_by_web_id("")
        await client.aclose()
