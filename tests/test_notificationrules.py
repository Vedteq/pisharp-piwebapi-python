"""Tests for AF Notification Rule operations (sync + async)."""

from __future__ import annotations

import httpx
import pytest

from tests.conftest import BASE_URL

NOTIFICATION_RULE_1 = {
    "WebId": "NR001",
    "Id": "guid-nr-001",
    "Name": "HighTempAlarm",
    "Description": "Notify when temperature exceeds threshold",
    "Path": "\\\\AF\\Production\\Pump-001|HighTempAlarm",
    "Status": "Enabled",
    "Criteria": "Temperature > 200",
    "TemplateName": "TempAlarm",
    "CategoryNames": ["Safety"],
    "Links": {"Self": f"{BASE_URL}/notificationrules/NR001"},
}

NOTIFICATION_RULE_2 = {
    "WebId": "NR002",
    "Id": "guid-nr-002",
    "Name": "LowPressureWarn",
    "Description": "Warning on low discharge pressure",
    "Path": "\\\\AF\\Production\\Pump-001|LowPressureWarn",
    "Status": "Disabled",
    "Criteria": "Pressure < 10",
    "TemplateName": "",
    "Links": {},
}

SUBSCRIBER_1 = {
    "WebId": "SUB001",
    "Name": "ops-team@example.com",
    "DeliveryChannel": "Email",
}

SUBSCRIBER_2 = {
    "WebId": "SUB002",
    "Name": "sms-oncall",
    "DeliveryChannel": "SMS",
}


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestNotificationRulesSync:
    """Sync AF NotificationRules operations."""

    def test_get_by_web_id(self, sync_client):
        client, mock = sync_client
        mock.get("/notificationrules/NR001").mock(
            return_value=httpx.Response(200, json=NOTIFICATION_RULE_1)
        )
        rule = client.notificationrules.get_by_web_id("NR001")
        assert rule.web_id == "NR001"
        assert rule.name == "HighTempAlarm"
        assert rule.status == "Enabled"

    def test_get_by_web_id_not_found(self, sync_client):
        client, mock = sync_client
        mock.get("/notificationrules/BOGUS").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        from pisharp_piwebapi.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            client.notificationrules.get_by_web_id("BOGUS")

    def test_get_by_web_id_invalid(self, sync_client):
        client, _ = sync_client
        with pytest.raises(ValueError, match="web_id"):
            client.notificationrules.get_by_web_id("")

    def test_get_by_path(self, sync_client):
        client, mock = sync_client
        mock.get("/notificationrules").mock(
            return_value=httpx.Response(200, json=NOTIFICATION_RULE_1)
        )
        rule = client.notificationrules.get_by_path(
            "\\\\AF\\Production\\Pump-001|HighTempAlarm"
        )
        assert rule.name == "HighTempAlarm"

    def test_get_by_element(self, sync_client):
        client, mock = sync_client
        mock.get("/elements/E0pump001/notificationrules").mock(
            return_value=httpx.Response(
                200,
                json={"Items": [NOTIFICATION_RULE_1, NOTIFICATION_RULE_2]},
            )
        )
        rules = client.notificationrules.get_by_element("E0pump001")
        assert len(rules) == 2
        assert rules[0].name == "HighTempAlarm"
        assert rules[1].name == "LowPressureWarn"

    def test_get_by_element_flat_array(self, sync_client):
        client, mock = sync_client
        mock.get("/elements/E0pump001/notificationrules").mock(
            return_value=httpx.Response(
                200, json=[NOTIFICATION_RULE_1]
            )
        )
        rules = client.notificationrules.get_by_element("E0pump001")
        assert len(rules) == 1

    def test_get_by_element_invalid_web_id(self, sync_client):
        client, _ = sync_client
        with pytest.raises(ValueError, match="element_web_id"):
            client.notificationrules.get_by_element("")

    def test_get_subscribers(self, sync_client):
        client, mock = sync_client
        mock.get(
            "/notificationrules/NR001/notificationrulesubscribers"
        ).mock(
            return_value=httpx.Response(
                200,
                json={"Items": [SUBSCRIBER_1, SUBSCRIBER_2]},
            )
        )
        subs = client.notificationrules.get_subscribers("NR001")
        assert len(subs) == 2
        assert subs[0]["Name"] == "ops-team@example.com"

    def test_get_subscribers_invalid_web_id(self, sync_client):
        client, _ = sync_client
        with pytest.raises(ValueError, match="web_id"):
            client.notificationrules.get_subscribers("")

    def test_delete(self, sync_client):
        client, mock = sync_client
        route = mock.delete("/notificationrules/NR001").mock(
            return_value=httpx.Response(204)
        )
        client.notificationrules.delete("NR001")
        assert route.called

    def test_delete_not_found(self, sync_client):
        client, mock = sync_client
        mock.delete("/notificationrules/BOGUS").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        from pisharp_piwebapi.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            client.notificationrules.delete("BOGUS")

    def test_delete_invalid_web_id(self, sync_client):
        client, _ = sync_client
        with pytest.raises(ValueError, match="web_id"):
            client.notificationrules.delete("")


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestNotificationRulesAsync:
    """Async AF NotificationRules operations."""

    async def test_get_by_web_id(self, async_client):
        client, mock = async_client
        mock.get("/notificationrules/NR001").mock(
            return_value=httpx.Response(200, json=NOTIFICATION_RULE_1)
        )
        rule = await client.notificationrules.get_by_web_id("NR001")
        assert rule.web_id == "NR001"
        assert rule.name == "HighTempAlarm"

    async def test_get_by_web_id_not_found(self, async_client):
        client, mock = async_client
        mock.get("/notificationrules/BOGUS").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        from pisharp_piwebapi.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await client.notificationrules.get_by_web_id("BOGUS")

    async def test_get_by_web_id_invalid(self, async_client):
        client, _ = async_client
        with pytest.raises(ValueError, match="web_id"):
            await client.notificationrules.get_by_web_id("")

    async def test_get_by_path(self, async_client):
        client, mock = async_client
        mock.get("/notificationrules").mock(
            return_value=httpx.Response(200, json=NOTIFICATION_RULE_1)
        )
        rule = await client.notificationrules.get_by_path(
            "\\\\AF\\Pump|HighTempAlarm"
        )
        assert rule.name == "HighTempAlarm"

    async def test_get_by_element(self, async_client):
        client, mock = async_client
        mock.get("/elements/E0pump001/notificationrules").mock(
            return_value=httpx.Response(
                200,
                json={"Items": [NOTIFICATION_RULE_1, NOTIFICATION_RULE_2]},
            )
        )
        rules = await client.notificationrules.get_by_element("E0pump001")
        assert len(rules) == 2

    async def test_get_by_element_invalid_web_id(self, async_client):
        client, _ = async_client
        with pytest.raises(ValueError, match="element_web_id"):
            await client.notificationrules.get_by_element("")

    async def test_get_subscribers(self, async_client):
        client, mock = async_client
        mock.get(
            "/notificationrules/NR001/notificationrulesubscribers"
        ).mock(
            return_value=httpx.Response(
                200,
                json={"Items": [SUBSCRIBER_1]},
            )
        )
        subs = await client.notificationrules.get_subscribers("NR001")
        assert len(subs) == 1

    async def test_delete(self, async_client):
        client, mock = async_client
        route = mock.delete("/notificationrules/NR001").mock(
            return_value=httpx.Response(204)
        )
        await client.notificationrules.delete("NR001")
        assert route.called

    async def test_delete_not_found(self, async_client):
        client, mock = async_client
        mock.delete("/notificationrules/BOGUS").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        from pisharp_piwebapi.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await client.notificationrules.delete("BOGUS")

    async def test_server_error(self, async_client):
        client, mock = async_client
        mock.get("/notificationrules/NR001").mock(
            return_value=httpx.Response(
                500, json={"Errors": ["Internal server error"]}
            )
        )
        from pisharp_piwebapi.exceptions import ServerError

        with pytest.raises(ServerError):
            await client.notificationrules.get_by_web_id("NR001")
