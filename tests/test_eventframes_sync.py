"""Integration tests for the EventFrames mixin (sync)."""

from __future__ import annotations

import httpx
import pytest
from conftest import (
    AF_DATABASE,
    ELEMENT_PUMP,
    EVENT_FRAME_1,
    EVENT_FRAME_2,
)

from pisharp_piwebapi.exceptions import AuthenticationError, NotFoundError
from pisharp_piwebapi.models import EventFrame

EF_WEB_ID = EVENT_FRAME_1["WebId"]
ELEM_WEB_ID = ELEMENT_PUMP["WebId"]
DB_WEB_ID = AF_DATABASE["WebId"]


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
        mock.get(f"/assetdatabases/{DB_WEB_ID}/eventframes").mock(
            return_value=httpx.Response(
                200, json={"Items": [EVENT_FRAME_1, EVENT_FRAME_2]}
            )
        )
        results = client.eventframes.search(DB_WEB_ID, name_filter="Motor*")
        assert len(results) == 2
        assert results[0].name == "Motor Overtemp"
        assert results[1].name == "Pressure Spike"

    def test_search_not_found(self, sync_client):
        client, mock = sync_client
        mock.get("/assetdatabases/BOGUS/eventframes").mock(
            return_value=httpx.Response(
                404, json={"Message": "Database not found."}
            )
        )
        with pytest.raises(NotFoundError):
            client.eventframes.search("BOGUS")

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
        route = mock.patch(f"/eventframes/{EF_WEB_ID}").mock(
            return_value=httpx.Response(204)
        )
        client.eventframes.acknowledge(EF_WEB_ID)
        assert route.called

    def test_create(self, sync_client):
        client, mock = sync_client
        route = mock.post(f"/assetdatabases/{DB_WEB_ID}/eventframes").mock(
            return_value=httpx.Response(201)
        )
        client.eventframes.create(
            DB_WEB_ID,
            "New Alert",
            start_time="2024-06-15T12:00:00Z",
            end_time="2024-06-15T12:30:00Z",
            description="Test event",
            severity="Warning",
        )
        assert route.called

    def test_create_with_ref_elements(self, sync_client):
        client, mock = sync_client
        route = mock.post(f"/assetdatabases/{DB_WEB_ID}/eventframes").mock(
            return_value=httpx.Response(201)
        )
        client.eventframes.create(
            DB_WEB_ID,
            "Element Alert",
            start_time="2024-06-15T12:00:00Z",
            end_time="2024-06-15T12:30:00Z",
            ref_element_web_ids=[ELEM_WEB_ID],
        )
        assert route.called
        body = route.calls[0].request.content
        import json
        parsed = json.loads(body)
        assert parsed["RefElementWebIds"] == [ELEM_WEB_ID]

    def test_delete(self, sync_client):
        client, mock = sync_client
        route = mock.delete(f"/eventframes/{EF_WEB_ID}").mock(
            return_value=httpx.Response(204)
        )
        client.eventframes.delete(EF_WEB_ID)
        assert route.called

    def test_get_by_web_id_not_found(self, sync_client):
        client, mock = sync_client
        mock.get("/eventframes/MISSING").mock(
            return_value=httpx.Response(
                404, json={"Message": "Event frame not found."}
            )
        )
        with pytest.raises(NotFoundError):
            client.eventframes.get_by_web_id("MISSING")

    def test_search_unauthorized(self, sync_client):
        client, mock = sync_client
        mock.get(f"/assetdatabases/{DB_WEB_ID}/eventframes").mock(
            return_value=httpx.Response(
                401, json={"Message": "Unauthorized."}
            )
        )
        with pytest.raises(AuthenticationError):
            client.eventframes.search(DB_WEB_ID)
