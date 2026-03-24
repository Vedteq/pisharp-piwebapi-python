"""Integration tests for the asynchronous AsyncPIWebAPIClient."""

from __future__ import annotations

import httpx
import respx
from conftest import (
    BASE_URL,
    BATCH_RESPONSE,
    CDIT158_POINT,
    CURRENT_VALUE,
    INTERPOLATED_VALUES,
    RECORDED_VALUES,
    SINUSOID_POINT,
)

from pisharp_piwebapi.models import PIPoint, StreamValue, StreamValues

WEB_ID = SINUSOID_POINT["WebId"]


# ── Points ──────────────────────────────────────────────────────────


class TestPointsAsync:
    async def test_get_by_path(self, async_client):
        client, mock = async_client
        mock.get("/points", params={"path": "\\\\SERVER\\sinusoid"}).mock(
            return_value=httpx.Response(200, json=SINUSOID_POINT)
        )
        point = await client.points.get_by_path(r"\\SERVER\sinusoid")
        assert isinstance(point, PIPoint)
        assert point.web_id == WEB_ID

    async def test_get_by_web_id(self, async_client):
        client, mock = async_client
        mock.get(f"/points/{WEB_ID}").mock(return_value=httpx.Response(200, json=SINUSOID_POINT))
        point = await client.points.get_by_web_id(WEB_ID)
        assert point.name == "sinusoid"

    async def test_search(self, async_client):
        client, mock = async_client
        ds_web_id = "DS001"
        mock.get(f"/dataservers/{ds_web_id}/points").mock(
            return_value=httpx.Response(200, json={"Items": [SINUSOID_POINT, CDIT158_POINT]})
        )
        results = await client.points.search(ds_web_id, name_filter="sinu*")
        assert len(results) == 2


# ── Streams ─────────────────────────────────────────────────────────


class TestStreamsAsync:
    async def test_get_value(self, async_client):
        client, mock = async_client
        mock.get(f"/streams/{WEB_ID}/value").mock(
            return_value=httpx.Response(200, json=CURRENT_VALUE)
        )
        val = await client.streams.get_value(WEB_ID)
        assert isinstance(val, StreamValue)
        assert val.value == 42.5

    async def test_get_recorded(self, async_client):
        client, mock = async_client
        mock.get(f"/streams/{WEB_ID}/recorded").mock(
            return_value=httpx.Response(200, json=RECORDED_VALUES)
        )
        vals = await client.streams.get_recorded(WEB_ID)
        assert isinstance(vals, StreamValues)
        assert len(vals) == 3

    async def test_get_interpolated(self, async_client):
        client, mock = async_client
        mock.get(f"/streams/{WEB_ID}/interpolated").mock(
            return_value=httpx.Response(200, json=INTERPOLATED_VALUES)
        )
        vals = await client.streams.get_interpolated(WEB_ID)
        assert len(vals) == 4

    async def test_update_value(self, async_client):
        client, mock = async_client
        route = mock.post(f"/streams/{WEB_ID}/value").mock(return_value=httpx.Response(202))
        await client.streams.update_value(WEB_ID, 99.9)
        assert route.called

    async def test_update_values_bulk(self, async_client):
        client, mock = async_client
        route = mock.post(f"/streams/{WEB_ID}/recorded").mock(return_value=httpx.Response(202))
        await client.streams.update_values(
            WEB_ID,
            [
                {"Value": 1.0, "Timestamp": "2024-06-15T11:00:00Z"},
                {"Value": 2.0, "Timestamp": "2024-06-15T11:05:00Z"},
            ],
        )
        assert route.called


# ── Batch ───────────────────────────────────────────────────────────


class TestBatchAsync:
    async def test_execute_batch(self, async_client):
        client, mock = async_client
        mock.post("/batch").mock(return_value=httpx.Response(200, json=BATCH_RESPONSE))
        result = await client.execute_batch(
            {
                "1": {"Method": "GET", "Resource": f"/points/{WEB_ID}"},
                "2": {"Method": "GET", "Resource": f"/streams/{WEB_ID}/value"},
            }
        )
        assert "1" in result
        assert result["1"]["Status"] == 200


# ── Pagination ──────────────────────────────────────────────────────


class TestPaginationAsync:
    async def test_get_all_pages_single_page(self, async_client):
        client, mock = async_client
        mock.get("/points/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "Items": [SINUSOID_POINT, CDIT158_POINT],
                    "Links": {},
                },
            )
        )
        items = await client.get_all_pages("/points/search", params={"q": "sinu*"})
        assert len(items) == 2

    async def test_get_all_pages_multi_page(self):
        page2_url = f"{BASE_URL}/points/search?startIndex=1"

        with respx.mock:
            respx.get(f"{BASE_URL}/points/search", params={"q": "sinu*"}).mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "Items": [SINUSOID_POINT],
                        "Links": {"Next": page2_url},
                    },
                )
            )
            respx.get(page2_url).mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "Items": [CDIT158_POINT],
                        "Links": {},
                    },
                )
            )
            from pisharp_piwebapi.client import AsyncPIWebAPIClient

            async with AsyncPIWebAPIClient(
                base_url=BASE_URL, username="admin", password="secret", verify_ssl=False
            ) as client:
                items = await client.get_all_pages("/points/search", params={"q": "sinu*"})
                assert len(items) == 2


# ── Context manager ─────────────────────────────────────────────────


class TestContextManagerAsync:
    async def test_async_context_manager(self):
        with respx.mock(base_url=BASE_URL):
            from pisharp_piwebapi.client import AsyncPIWebAPIClient

            async with AsyncPIWebAPIClient(
                base_url=BASE_URL,
                username="admin",
                password="secret",
                verify_ssl=False,
            ) as client:
                assert client is not None
