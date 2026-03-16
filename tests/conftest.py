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
