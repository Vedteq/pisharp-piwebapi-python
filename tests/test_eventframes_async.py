"""Integration tests for the EventFrames mixin (async)."""

from __future__ import annotations

import httpx
import pytest
from conftest import (
    AF_DATABASE,
    ELEMENT_PUMP,
    EVENT_FRAME_1,
    EVENT_FRAME_2,
)

from pisharp_piwebapi.exceptions import NotFoundError
from pisharp_piwebapi.models import EventFrame

EF_WEB_ID = EVENT_FRAME_1["WebId"]
ELEM_WEB_ID = ELEMENT_PUMP["WebId"]
DB_WEB_ID = AF_DATABASE["WebId"]


class TestEventFramesAsync:
    async def test_get_by_web_id(self, async_client):
        client, mock = async_client
        mock.get(f"/eventframes/{EF_WEB_ID}").mock(
            return_value=httpx.Response(200, json=EVENT_FRAME_1)
        )
        ef = await client.eventframes.get_by_web_id(EF_WEB_ID)
        assert isinstance(ef, EventFrame)
        assert ef.name == "Motor Overtemp"

    async def test_search(self, async_client):
        client, mock = async_client
        mock.get(f"/assetdatabases/{DB_WEB_ID}/eventframes").mock(
            return_value=httpx.Response(
                200, json={"Items": [EVENT_FRAME_1, EVENT_FRAME_2]}
            )
        )
        results = await client.eventframes.search(
            DB_WEB_ID, name_filter="Motor*"
        )
        assert len(results) == 2

    async def test_search_not_found(self, async_client):
        client, mock = async_client
        mock.get("/assetdatabases/BOGUS/eventframes").mock(
            return_value=httpx.Response(
                404, json={"Message": "Database not found."}
            )
        )
        with pytest.raises(NotFoundError):
            await client.eventframes.search("BOGUS")

    async def test_get_by_element(self, async_client):
        client, mock = async_client
        mock.get(f"/elements/{ELEM_WEB_ID}/eventframes").mock(
            return_value=httpx.Response(200, json={"Items": [EVENT_FRAME_1]})
        )
        results = await client.eventframes.get_by_element(ELEM_WEB_ID)
        assert len(results) == 1

    async def test_acknowledge(self, async_client):
        client, mock = async_client
        route = mock.patch(f"/eventframes/{EF_WEB_ID}").mock(
            return_value=httpx.Response(204)
        )
        await client.eventframes.acknowledge(EF_WEB_ID)
        assert route.called

    async def test_create(self, async_client):
        client, mock = async_client
        route = mock.post(f"/assetdatabases/{DB_WEB_ID}/eventframes").mock(
            return_value=httpx.Response(201)
        )
        await client.eventframes.create(
            DB_WEB_ID,
            "New Alert",
            start_time="2024-06-15T12:00:00Z",
            end_time="2024-06-15T12:30:00Z",
        )
        assert route.called

    async def test_delete(self, async_client):
        client, mock = async_client
        route = mock.delete(f"/eventframes/{EF_WEB_ID}").mock(
            return_value=httpx.Response(204)
        )
        await client.eventframes.delete(EF_WEB_ID)
        assert route.called
