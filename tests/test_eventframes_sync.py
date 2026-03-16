"""Integration tests for the EventFrames mixin (sync)."""

from __future__ import annotations

import httpx
from conftest import (
    ELEMENT_PUMP,
    EVENT_FRAME_1,
    EVENT_FRAME_2,
)

from pisharp_piwebapi.models import EventFrame

EF_WEB_ID = EVENT_FRAME_1["WebId"]
ELEM_WEB_ID = ELEMENT_PUMP["WebId"]


class TestEventFramesSync:
    def test_get_by_web_id(self, sync_client):
        client, mock = sync_client
        mock.get(f"/eventframes/{EF_WEB_ID}").mock(
            return_value=httpx.Response(200, json=EVENT_FRAME_1)
        )
        ef = client.eventframes.get_by_web_id(EF_WEB_ID)
        assert isinstance(ef, EventFrame)
        assert ef.name == "Motor Overtemp"
        assert ef.severity == "Major"
        assert ef.is_acknowledged is False

    def test_search(self, sync_client):
        client, mock = sync_client
        mock.get("/eventframes/search").mock(
            return_value=httpx.Response(200, json={"Items": [EVENT_FRAME_1, EVENT_FRAME_2]})
        )
        results = client.eventframes.search("Motor*")
        assert len(results) == 2
        assert results[0].name == "Motor Overtemp"
        assert results[1].name == "Pressure Spike"

    def test_get_by_element(self, sync_client):
        client, mock = sync_client
        mock.get(f"/elements/{ELEM_WEB_ID}/eventframes").mock(
            return_value=httpx.Response(200, json={"Items": [EVENT_FRAME_1]})
        )
        results = client.eventframes.get_by_element(ELEM_WEB_ID)
        assert len(results) == 1
        assert results[0].web_id == EF_WEB_ID

    def test_acknowledge(self, sync_client):
        client, mock = sync_client
        route = mock.patch(f"/eventframes/{EF_WEB_ID}").mock(return_value=httpx.Response(204))
        client.eventframes.acknowledge(EF_WEB_ID)
        assert route.called

    def test_create(self, sync_client):
        client, mock = sync_client
        route = mock.post(f"/elements/{ELEM_WEB_ID}/eventframes").mock(
            return_value=httpx.Response(201)
        )
        client.eventframes.create(
            ELEM_WEB_ID,
            "New Alert",
            start_time="2024-06-15T12:00:00Z",
            end_time="2024-06-15T12:30:00Z",
            description="Test event",
            severity="Warning",
        )
        assert route.called

    def test_delete(self, sync_client):
        client, mock = sync_client
        route = mock.delete(f"/eventframes/{EF_WEB_ID}").mock(return_value=httpx.Response(204))
        client.eventframes.delete(EF_WEB_ID)
        assert route.called
