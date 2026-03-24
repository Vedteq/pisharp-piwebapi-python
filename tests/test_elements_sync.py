"""Integration tests for the Elements mixin (sync)."""

from __future__ import annotations

import httpx
from conftest import (
    ATTRIBUTE_SPEED,
    ATTRIBUTE_TEMP,
    ELEMENT_MOTOR,
    ELEMENT_PUMP,
)

from pisharp_piwebapi.models import PIAttribute, PIElement

ELEM_WEB_ID = ELEMENT_PUMP["WebId"]


class TestElementsSync:
    def test_get_element_by_path(self, sync_client):
        client, mock = sync_client
        mock.get("/elements", params={"path": "\\\\AF\\Production\\Pump-001"}).mock(
            return_value=httpx.Response(200, json=ELEMENT_PUMP)
        )
        elem = client.elements.get_element_by_path(r"\\AF\Production\Pump-001")
        assert isinstance(elem, PIElement)
        assert elem.name == "Pump-001"
        assert elem.template_name == "Pump"

    def test_get_element(self, sync_client):
        client, mock = sync_client
        mock.get(f"/elements/{ELEM_WEB_ID}").mock(
            return_value=httpx.Response(200, json=ELEMENT_PUMP)
        )
        elem = client.elements.get_element(ELEM_WEB_ID)
        assert elem.web_id == ELEM_WEB_ID
        assert elem.has_children is True

    def test_get_child_elements(self, sync_client):
        client, mock = sync_client
        mock.get(f"/elements/{ELEM_WEB_ID}/elements").mock(
            return_value=httpx.Response(200, json={"Items": [ELEMENT_MOTOR]})
        )
        children = client.elements.get_child_elements(ELEM_WEB_ID)
        assert len(children) == 1
        assert children[0].name == "Motor-001"

    def test_get_attributes(self, sync_client):
        client, mock = sync_client
        mock.get(f"/elements/{ELEM_WEB_ID}/attributes").mock(
            return_value=httpx.Response(200, json={"Items": [ATTRIBUTE_TEMP, ATTRIBUTE_SPEED]})
        )
        attrs = client.elements.get_attributes(ELEM_WEB_ID)
        assert len(attrs) == 2
        assert isinstance(attrs[0], PIAttribute)
        assert attrs[0].name == "Temperature"
        assert attrs[1].name == "Speed"

    def test_create_element(self, sync_client):
        client, mock = sync_client
        route = mock.post(f"/elements/{ELEM_WEB_ID}/elements").mock(
            return_value=httpx.Response(201)
        )
        client.elements.create_element(
            ELEM_WEB_ID,
            "Valve-001",
            description="Inlet valve",
            template_name="Valve",
        )
        assert route.called

    def test_delete_element(self, sync_client):
        client, mock = sync_client
        route = mock.delete(f"/elements/{ELEM_WEB_ID}").mock(return_value=httpx.Response(204))
        client.elements.delete_element(ELEM_WEB_ID)
        assert route.called
