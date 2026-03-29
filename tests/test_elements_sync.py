"""Integration tests for the Elements mixin (sync)."""

from __future__ import annotations

import httpx
import pytest
from conftest import (
    AF_DATABASE,
    ATTRIBUTE_SPEED,
    ATTRIBUTE_TEMP,
    ELEMENT_MOTOR,
    ELEMENT_PUMP,
)

from pisharp_piwebapi.exceptions import NotFoundError
from pisharp_piwebapi.models import PIAttribute, PIElement, StreamValue

ELEM_WEB_ID = ELEMENT_PUMP["WebId"]
DB_WEB_ID = AF_DATABASE["WebId"]


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

    def test_get_elements_default_does_not_send_search_full_hierarchy(self, sync_client):
        """get_elements with default args does not send the searchFullHierarchy param."""
        client, mock = sync_client
        route = mock.get(f"/assetdatabases/{DB_WEB_ID}/elements").mock(
            return_value=httpx.Response(200, json={"Items": [ELEMENT_PUMP]})
        )
        client.elements.get_elements(DB_WEB_ID)
        raw_query = route.calls.last.request.url.query.decode()
        assert "searchFullHierarchy" not in raw_query

    def test_get_elements_search_full_hierarchy_true(self, sync_client):
        """get_elements passes searchFullHierarchy=True when requested."""
        client, mock = sync_client
        route = mock.get(f"/assetdatabases/{DB_WEB_ID}/elements").mock(
            return_value=httpx.Response(
                200, json={"Items": [ELEMENT_PUMP, ELEMENT_MOTOR]}
            )
        )
        result = client.elements.get_elements(DB_WEB_ID, search_full_hierarchy=True)
        raw_query = route.calls.last.request.url.query.decode()
        assert "searchFullHierarchy=true" in raw_query
        assert len(result) == 2
        assert all(isinstance(e, PIElement) for e in result)

    def test_get_attribute_by_path(self, sync_client):
        client, mock = sync_client
        attr_path = r"\\AF\Production\Pump-001|Temperature"
        mock.get(
            "/attributes",
            params={"path": "\\\\AF\\Production\\Pump-001|Temperature"},
        ).mock(return_value=httpx.Response(200, json=ATTRIBUTE_TEMP))
        attr = client.elements.get_attribute_by_path(attr_path)
        assert isinstance(attr, PIAttribute)
        assert attr.name == "Temperature"
        assert attr.web_id == "A0temp001"

    def test_get_attribute_by_path_not_found(self, sync_client):
        client, mock = sync_client
        mock.get("/attributes").mock(
            return_value=httpx.Response(
                404, json={"Message": "Attribute not found."}
            )
        )
        with pytest.raises(NotFoundError):
            client.elements.get_attribute_by_path(
                r"\\AF\Production\Pump-001|Nonexistent"
            )

    def test_create_attribute(self, sync_client):
        client, mock = sync_client
        route = mock.post(f"/elements/{ELEM_WEB_ID}/attributes").mock(
            return_value=httpx.Response(201)
        )
        client.elements.create_attribute(
            ELEM_WEB_ID,
            "Vibration",
            description="Vibration sensor",
            type_qualifier="Double",
        )
        assert route.called
        body = route.calls.last.request.read()
        import json

        payload = json.loads(body)
        assert payload["Name"] == "Vibration"
        assert payload["Description"] == "Vibration sensor"
        assert payload["TypeQualifier"] == "Double"

    def test_create_attribute_minimal(self, sync_client):
        client, mock = sync_client
        route = mock.post(f"/elements/{ELEM_WEB_ID}/attributes").mock(
            return_value=httpx.Response(201)
        )
        client.elements.create_attribute(ELEM_WEB_ID, "Pressure")
        assert route.called
        import json

        payload = json.loads(route.calls.last.request.read())
        assert payload == {"Name": "Pressure"}

    def test_update_attribute(self, sync_client):
        client, mock = sync_client
        attr_wid = ATTRIBUTE_TEMP["WebId"]
        route = mock.patch(f"/attributes/{attr_wid}").mock(
            return_value=httpx.Response(204)
        )
        client.elements.update_attribute(
            attr_wid, {"Description": "Updated description"}
        )
        assert route.called

    def test_update_attribute_not_found(self, sync_client):
        client, mock = sync_client
        mock.patch("/attributes/BOGUS").mock(
            return_value=httpx.Response(
                404, json={"Message": "Attribute not found."}
            )
        )
        with pytest.raises(NotFoundError):
            client.elements.update_attribute(
                "BOGUS", {"Description": "nope"}
            )

    def test_delete_attribute(self, sync_client):
        client, mock = sync_client
        attr_wid = ATTRIBUTE_TEMP["WebId"]
        route = mock.delete(f"/attributes/{attr_wid}").mock(
            return_value=httpx.Response(204)
        )
        client.elements.delete_attribute(attr_wid)
        assert route.called

    def test_delete_attribute_not_found(self, sync_client):
        client, mock = sync_client
        mock.delete("/attributes/BOGUS").mock(
            return_value=httpx.Response(
                404, json={"Message": "Attribute not found."}
            )
        )
        with pytest.raises(NotFoundError):
            client.elements.delete_attribute("BOGUS")

    def test_get_attribute_value(self, sync_client):
        client, mock = sync_client
        attr_wid = ATTRIBUTE_TEMP["WebId"]
        value_response = {
            "Timestamp": "2024-06-15T12:00:00Z",
            "Value": 72.5,
            "UnitsAbbreviation": "degC",
            "Good": True,
            "Questionable": False,
            "Substituted": False,
            "Annotated": False,
        }
        mock.get(f"/attributes/{attr_wid}/value").mock(
            return_value=httpx.Response(200, json=value_response)
        )
        val = client.elements.get_attribute_value(attr_wid)
        assert isinstance(val, StreamValue)
        assert val.value == 72.5
        assert val.good is True

    def test_get_attribute_value_not_found(self, sync_client):
        client, mock = sync_client
        mock.get("/attributes/BOGUS/value").mock(
            return_value=httpx.Response(
                404, json={"Message": "Attribute not found."}
            )
        )
        with pytest.raises(NotFoundError):
            client.elements.get_attribute_value("BOGUS")

    def test_set_attribute_value_scalar(self, sync_client):
        client, mock = sync_client
        attr_wid = ATTRIBUTE_TEMP["WebId"]
        route = mock.put(f"/attributes/{attr_wid}/value").mock(
            return_value=httpx.Response(204)
        )
        client.elements.set_attribute_value(attr_wid, 99.9)
        assert route.called
        import json

        payload = json.loads(route.calls.last.request.read())
        assert payload == {"Value": 99.9}

    def test_set_attribute_value_dict(self, sync_client):
        client, mock = sync_client
        attr_wid = ATTRIBUTE_TEMP["WebId"]
        route = mock.put(f"/attributes/{attr_wid}/value").mock(
            return_value=httpx.Response(204)
        )
        body = {"Value": 42, "Timestamp": "2024-01-01T00:00:00Z"}
        client.elements.set_attribute_value(attr_wid, body)
        assert route.called
        import json

        payload = json.loads(route.calls.last.request.read())
        assert payload == body

    def test_update_element(self, sync_client):
        client, mock = sync_client
        route = mock.patch(f"/elements/{ELEM_WEB_ID}").mock(
            return_value=httpx.Response(204)
        )
        client.elements.update_element(
            ELEM_WEB_ID, {"Description": "Updated pump"}
        )
        assert route.called

    def test_update_element_not_found(self, sync_client):
        client, mock = sync_client
        mock.patch("/elements/BOGUS").mock(
            return_value=httpx.Response(
                404, json={"Message": "Element not found."}
            )
        )
        with pytest.raises(NotFoundError):
            client.elements.update_element("BOGUS", {"Name": "nope"})
