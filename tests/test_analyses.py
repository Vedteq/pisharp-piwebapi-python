"""Tests for AF Analysis operations (sync + async)."""

from __future__ import annotations

import httpx
import pytest
import respx

from tests.conftest import BASE_URL

ANALYSIS_1 = {
    "WebId": "AN001",
    "Id": "guid-an-001",
    "Name": "AvgTemp",
    "Description": "Average temperature calculation",
    "Path": "\\\\AF\\Production\\Pump-001|AvgTemp",
    "AnalysisRulePlugInName": "PerformanceEquation",
    "Status": "Enabled",
    "TemplateName": "TempAnalysis",
    "IsConfigured": True,
    "HasNotification": False,
    "Links": {"Self": f"{BASE_URL}/analyses/AN001"},
}

ANALYSIS_2 = {
    "WebId": "AN002",
    "Id": "guid-an-002",
    "Name": "PressureCalc",
    "Description": "Pressure rollup",
    "Path": "\\\\AF\\Production\\Pump-001|PressureCalc",
    "AnalysisRulePlugInName": "Rollup",
    "Status": "Disabled",
    "TemplateName": "",
    "IsConfigured": False,
    "Links": {},
}


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestAnalysesSync:
    """Sync AF Analyses operations."""

    def test_get_by_web_id(self, sync_client):
        client, mock = sync_client
        mock.get(f"/analyses/AN001").mock(
            return_value=httpx.Response(200, json=ANALYSIS_1)
        )
        analysis = client.analyses.get_by_web_id("AN001")
        assert analysis.web_id == "AN001"
        assert analysis.name == "AvgTemp"
        assert analysis.status == "Enabled"

    def test_get_by_web_id_not_found(self, sync_client):
        client, mock = sync_client
        mock.get(f"/analyses/BOGUS").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        from pisharp_piwebapi.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            client.analyses.get_by_web_id("BOGUS")

    def test_get_by_web_id_invalid(self, sync_client):
        client, _ = sync_client
        with pytest.raises(ValueError, match="web_id"):
            client.analyses.get_by_web_id("")

    def test_get_by_path(self, sync_client):
        client, mock = sync_client
        mock.get("/analyses").mock(
            return_value=httpx.Response(200, json=ANALYSIS_1)
        )
        analysis = client.analyses.get_by_path(
            "\\\\AF\\Production\\Pump-001|AvgTemp"
        )
        assert analysis.name == "AvgTemp"

    def test_get_by_element(self, sync_client):
        client, mock = sync_client
        mock.get("/elements/E0pump001/analyses").mock(
            return_value=httpx.Response(
                200, json={"Items": [ANALYSIS_1, ANALYSIS_2]}
            )
        )
        analyses = client.analyses.get_by_element("E0pump001")
        assert len(analyses) == 2
        assert analyses[0].name == "AvgTemp"
        assert analyses[1].name == "PressureCalc"

    def test_get_by_element_flat_array(self, sync_client):
        client, mock = sync_client
        mock.get("/elements/E0pump001/analyses").mock(
            return_value=httpx.Response(200, json=[ANALYSIS_1])
        )
        analyses = client.analyses.get_by_element("E0pump001")
        assert len(analyses) == 1

    def test_get_by_element_invalid_web_id(self, sync_client):
        client, _ = sync_client
        with pytest.raises(ValueError, match="element_web_id"):
            client.analyses.get_by_element("")

    def test_update(self, sync_client):
        client, mock = sync_client
        route = mock.patch("/analyses/AN001").mock(
            return_value=httpx.Response(204)
        )
        client.analyses.update(
            "AN001", name="AvgTemp_v2", status="Disabled"
        )
        assert route.called
        body = route.calls[0].request.content
        import json

        parsed = json.loads(body)
        assert parsed["Name"] == "AvgTemp_v2"
        assert parsed["Status"] == "Disabled"

    def test_update_no_op(self, sync_client):
        """Update with no fields should return without HTTP request."""
        client, _mock = sync_client
        # No route registered — if update() tries to call the server,
        # respx will raise ConnectionError.
        client.analyses.update("AN001")

    def test_update_with_extra_fields(self, sync_client):
        client, mock = sync_client
        route = mock.patch("/analyses/AN001").mock(
            return_value=httpx.Response(204)
        )
        client.analyses.update(
            "AN001",
            extra_fields={"Priority": "High"},
        )
        import json

        parsed = json.loads(route.calls[0].request.content)
        assert parsed["Priority"] == "High"

    def test_delete(self, sync_client):
        client, mock = sync_client
        route = mock.delete("/analyses/AN001").mock(
            return_value=httpx.Response(204)
        )
        client.analyses.delete("AN001")
        assert route.called

    def test_delete_not_found(self, sync_client):
        client, mock = sync_client
        mock.delete("/analyses/BOGUS").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        from pisharp_piwebapi.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            client.analyses.delete("BOGUS")

    def test_delete_invalid_web_id(self, sync_client):
        client, _ = sync_client
        with pytest.raises(ValueError, match="web_id"):
            client.analyses.delete("")


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestAnalysesAsync:
    """Async AF Analyses operations."""

    async def test_get_by_web_id(self, async_client):
        client, mock = async_client
        mock.get(f"/analyses/AN001").mock(
            return_value=httpx.Response(200, json=ANALYSIS_1)
        )
        analysis = await client.analyses.get_by_web_id("AN001")
        assert analysis.web_id == "AN001"
        assert analysis.name == "AvgTemp"

    async def test_get_by_web_id_not_found(self, async_client):
        client, mock = async_client
        mock.get(f"/analyses/BOGUS").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        from pisharp_piwebapi.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await client.analyses.get_by_web_id("BOGUS")

    async def test_get_by_web_id_invalid(self, async_client):
        client, _ = async_client
        with pytest.raises(ValueError, match="web_id"):
            await client.analyses.get_by_web_id("")

    async def test_get_by_path(self, async_client):
        client, mock = async_client
        mock.get("/analyses").mock(
            return_value=httpx.Response(200, json=ANALYSIS_1)
        )
        analysis = await client.analyses.get_by_path(
            "\\\\AF\\Production\\Pump-001|AvgTemp"
        )
        assert analysis.name == "AvgTemp"

    async def test_get_by_element(self, async_client):
        client, mock = async_client
        mock.get("/elements/E0pump001/analyses").mock(
            return_value=httpx.Response(
                200, json={"Items": [ANALYSIS_1, ANALYSIS_2]}
            )
        )
        analyses = await client.analyses.get_by_element("E0pump001")
        assert len(analyses) == 2

    async def test_get_by_element_invalid_web_id(self, async_client):
        client, _ = async_client
        with pytest.raises(ValueError, match="element_web_id"):
            await client.analyses.get_by_element("")

    async def test_update(self, async_client):
        client, mock = async_client
        route = mock.patch("/analyses/AN001").mock(
            return_value=httpx.Response(204)
        )
        await client.analyses.update(
            "AN001", description="Updated desc"
        )
        assert route.called

    async def test_update_no_op(self, async_client):
        """Update with no fields should return without HTTP request."""
        client, _mock = async_client
        await client.analyses.update("AN001")

    async def test_delete(self, async_client):
        client, mock = async_client
        route = mock.delete("/analyses/AN001").mock(
            return_value=httpx.Response(204)
        )
        await client.analyses.delete("AN001")
        assert route.called

    async def test_delete_not_found(self, async_client):
        client, mock = async_client
        mock.delete("/analyses/BOGUS").mock(
            return_value=httpx.Response(
                404, json={"Errors": ["Not found"]}
            )
        )
        from pisharp_piwebapi.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await client.analyses.delete("BOGUS")

    async def test_server_error(self, async_client):
        """500 errors should raise ServerError."""
        client, mock = async_client
        mock.get("/analyses/AN001").mock(
            return_value=httpx.Response(
                500, json={"Errors": ["Internal server error"]}
            )
        )
        from pisharp_piwebapi.exceptions import ServerError

        with pytest.raises(ServerError):
            await client.analyses.get_by_web_id("AN001")
