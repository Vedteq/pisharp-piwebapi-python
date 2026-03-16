"""Shared fixtures for integration tests."""

from __future__ import annotations

import pytest
import respx

from pisharp_piwebapi.client import AsyncPIWebAPIClient, PIWebAPIClient

BASE_URL = "https://piserver.example.com/piwebapi"

# --- Canonical API response payloads ---

SINUSOID_POINT = {
    "WebId": "P0HkV9SiKIkykmpIlkJfOVdg5AUAAAAU0VSVkVSXFNJTlVTT0lE",
    "Id": 1,
    "Name": "sinusoid",
    "Path": "\\\\SERVER\\sinusoid",
    "Descriptor": "12 Hour Sinusoid",
    "PointClass": "classic",
    "PointType": "Float32",
    "EngineeringUnits": "",
    "Future": False,
    "Links": {
        "Self": f"{BASE_URL}/points/P0HkV9SiKIkykmpIlkJfOVdg5AUAAAAU0VSVkVSXFNJTlVTT0lE",
    },
}

CDIT158_POINT = {
    "WebId": "P0cdit158webid",
    "Id": 2,
    "Name": "cdit158",
    "Path": "\\\\SERVER\\cdit158",
    "Descriptor": "Test point",
    "PointClass": "classic",
    "PointType": "Int32",
    "EngineeringUnits": "psi",
    "Future": False,
    "Links": {},
}

CURRENT_VALUE = {
    "Timestamp": "2024-06-15T12:00:00Z",
    "Value": 42.5,
    "UnitsAbbreviation": "degC",
    "Good": True,
    "Questionable": False,
    "Substituted": False,
    "Annotated": False,
}

RECORDED_VALUES = {
    "WebId": "P0HkV9SiKIkykmpIlkJfOVdg5AUAAAAU0VSVkVSXFNJTlVTT0lE",
    "Name": "sinusoid",
    "Path": "",
    "Items": [
        {"Timestamp": "2024-06-15T11:00:00Z", "Value": 10.0, "Good": True},
        {"Timestamp": "2024-06-15T11:30:00Z", "Value": 20.0, "Good": True},
        {"Timestamp": "2024-06-15T12:00:00Z", "Value": 30.0, "Good": True},
    ],
    "UnitsAbbreviation": "degC",
    "Links": {},
}

INTERPOLATED_VALUES = {
    "WebId": "P0HkV9SiKIkykmpIlkJfOVdg5AUAAAAU0VSVkVSXFNJTlVTT0lE",
    "Name": "sinusoid",
    "Path": "",
    "Items": [
        {"Timestamp": "2024-06-15T11:00:00Z", "Value": 10.0, "Good": True},
        {"Timestamp": "2024-06-15T11:10:00Z", "Value": 15.0, "Good": True},
        {"Timestamp": "2024-06-15T11:20:00Z", "Value": 20.0, "Good": True},
        {"Timestamp": "2024-06-15T11:30:00Z", "Value": 25.0, "Good": True},
    ],
    "UnitsAbbreviation": "degC",
    "Links": {},
}

BATCH_RESPONSE = {
    "1": {"Status": 200, "Headers": {}, "Content": SINUSOID_POINT},
    "2": {"Status": 200, "Headers": {}, "Content": CURRENT_VALUE},
}

ELEMENT_PUMP = {
    "WebId": "E0pump001",
    "Name": "Pump-001",
    "Path": "\\\\AF\\Production\\Pump-001",
    "Description": "Main coolant pump",
    "TemplateName": "Pump",
    "HasChildren": True,
    "Links": {"Self": f"{BASE_URL}/elements/E0pump001"},
}

ELEMENT_MOTOR = {
    "WebId": "E0motor001",
    "Name": "Motor-001",
    "Path": "\\\\AF\\Production\\Pump-001\\Motor-001",
    "Description": "Pump drive motor",
    "TemplateName": "Motor",
    "HasChildren": False,
    "Links": {},
}

ATTRIBUTE_TEMP = {
    "WebId": "A0temp001",
    "Name": "Temperature",
    "Path": "\\\\AF\\Production\\Pump-001|Temperature",
    "Description": "Bearing temperature",
    "Type": "PIPoint",
    "Value": None,
    "Links": {},
}

ATTRIBUTE_SPEED = {
    "WebId": "A0speed001",
    "Name": "Speed",
    "Path": "\\\\AF\\Production\\Pump-001|Speed",
    "Description": "Motor speed",
    "Type": "PIPoint",
    "Value": None,
    "Links": {},
}

EVENT_FRAME_1 = {
    "WebId": "EF0001",
    "Id": "ef-guid-001",
    "Name": "Motor Overtemp",
    "Description": "Motor exceeded temperature threshold",
    "StartTime": "2024-06-15T08:00:00Z",
    "EndTime": "2024-06-15T09:30:00Z",
    "TemplateName": "OverTemp",
    "Severity": "Major",
    "IsAcknowledged": False,
    "CanBeAcknowledged": True,
    "AreValuesCaptured": True,
    "RefElementWebIds": ["E0pump001"],
    "Links": {"Self": f"{BASE_URL}/eventframes/EF0001"},
}

EVENT_FRAME_2 = {
    "WebId": "EF0002",
    "Id": "ef-guid-002",
    "Name": "Pressure Spike",
    "Description": "Discharge pressure exceeded limit",
    "StartTime": "2024-06-15T10:00:00Z",
    "EndTime": "2024-06-15T10:15:00Z",
    "TemplateName": "PressureAlarm",
    "Severity": "Minor",
    "IsAcknowledged": True,
    "CanBeAcknowledged": True,
    "Links": {},
}


ASSET_SERVER = {
    "WebId": "AS001",
    "Id": "guid-as-001",
    "Name": "MyAFServer",
    "Description": "Production AF Server",
    "IsConnected": True,
    "ServerVersion": "2.10.9",
    "Links": {"Self": f"{BASE_URL}/assetservers/AS001"},
}

DATA_SERVER = {
    "WebId": "DS001",
    "Id": "guid-ds-001",
    "Name": "MyPIServer",
    "Path": "\\\\MyPIServer",
    "IsConnected": True,
    "ServerVersion": "2023 SP1",
    "Links": {"Self": f"{BASE_URL}/dataservers/DS001"},
}

AF_DATABASE = {
    "WebId": "DB001",
    "Name": "Production",
    "Path": "\\\\MyAFServer\\Production",
    "Description": "Production database",
    "Links": {"Self": f"{BASE_URL}/assetdatabases/DB001"},
}


@pytest.fixture()
def sync_client():
    """A PIWebAPIClient backed by a respx-mocked transport."""
    with respx.mock(base_url=BASE_URL) as mock:
        client = PIWebAPIClient(
            base_url=BASE_URL,
            username="admin",
            password="secret",
            verify_ssl=False,
        )
        yield client, mock
        client.close()


@pytest.fixture()
async def async_client():
    """An AsyncPIWebAPIClient backed by a respx-mocked transport."""
    with respx.mock(base_url=BASE_URL) as mock:
        client = AsyncPIWebAPIClient(
            base_url=BASE_URL,
            username="admin",
            password="secret",
            verify_ssl=False,
        )
        yield client, mock
        await client.aclose()
