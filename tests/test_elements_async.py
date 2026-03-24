"""Integration tests for the Elements mixin (async)."""

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


class TestElementsAsync:
    async def test_get_element_by_path(self, async_client):
        client, mock = async_client
        mock.get("/elements", params={"path": "\\\\AF\\Production\\Pump-001"}).mock(
            return_value=httpx.Response(200, json=ELEMENT_PUMP)
        )
        elem = await client.elements.get_element_by_path(r"\\AF\Production\Pump-001")
        assert isinstance(elem, PIElement)
        assert elem.name == "Pump-001"

    async def test_get_element(self, async_client):
        client, mock = async_client
        mock.get(f"/elements/{ELEM_WEB_ID}").mock(
            return_value=httpx.Response(200, json=ELEMENT_PUMP)
        )
        elem = await client.elements.get_element(ELEM_WEB_ID)
        assert elem.web_id == ELEM_WEB_ID

    async def test_get_child_elements(self, async_client):
        client, mock = async_client
        mock.get(f"/elements/{ELEM_WEB_ID}/elements").mock(
            return_value=httpx.Response(200, json={"Items": [ELEMENT_MOTOR]})
        )
        children = await client.elements.get_child_elements(ELEM_WEB_ID)
        assert len(children) == 1

    async def test_get_attributes(self, async_client):
        client, mock = async_client
        mock.get(f"/elements/{ELEM_WEB_ID}/attributes").mock(
            return_value=httpx.Response(200, json={"Items": [ATTRIBUTE_TEMP, ATTRIBUTE_SPEED]})
        )
        attrs = await client.elements.get_attributes(ELEM_WEB_ID)
        assert len(attrs) == 2
        assert isinstance(attrs[0], PIAttribute)

    async def test_create_element(self, async_client):
        client, mock = async_client
        route = mock.post(f"/elements/{ELEM_WEB_ID}/elements").mock(
            return_value=httpx.Response(201)
        )
        await client.elements.create_element(ELEM_WEB_ID, "Valve-001")
        assert route.called

    async def test_delete_element(self, async_client):
        client, mock = async_client
        route = mock.delete(f"/elements/{ELEM_WEB_ID}").mock(return_value=httpx.Response(204))
        await client.elements.delete_element(ELEM_WEB_ID)
        assert route.called
