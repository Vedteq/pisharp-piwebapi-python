"""Tests for Pydantic response models."""

from datetime import datetime, timezone

from pisharp_piwebapi.models import PIPoint, StreamValue, StreamValues


def test_pi_point_from_api_response():
    data = {
        "WebId": "P0123456789",
        "Id": 1,
        "Name": "sinusoid",
        "Path": "\\\\SERVER\\sinusoid",
        "Descriptor": "12 Hour Sinusoid",
        "PointClass": "classic",
        "PointType": "Float32",
        "EngineeringUnits": "",
        "Future": False,
        "Links": {"Self": "https://server/piwebapi/points/P0123456789"},
    }
    point = PIPoint.model_validate(data)
    assert point.web_id == "P0123456789"
    assert point.name == "sinusoid"
    assert point.path == "\\\\SERVER\\sinusoid"
    assert point.point_type == "Float32"


def test_stream_value_from_api_response():
    data = {
        "Timestamp": "2024-01-15T10:30:00Z",
        "Value": 42.5,
        "UnitsAbbreviation": "degC",
        "Good": True,
        "Questionable": False,
        "Substituted": False,
        "Annotated": False,
    }
    value = StreamValue.model_validate(data)
    assert value.value == 42.5
    assert value.good is True
    assert value.units_abbreviation == "degC"
    assert isinstance(value.timestamp, datetime)


def test_stream_values_iterable():
    data = {
        "WebId": "S0123",
        "Name": "sinusoid",
        "Path": "",
        "Items": [
            {"Timestamp": "2024-01-15T10:00:00Z", "Value": 1.0, "Good": True},
            {"Timestamp": "2024-01-15T10:05:00Z", "Value": 2.0, "Good": True},
            {"Timestamp": "2024-01-15T10:10:00Z", "Value": 3.0, "Good": True},
        ],
    }
    values = StreamValues.model_validate(data)
    assert len(values) == 3
    items = list(values)
    assert items[0].value == 1.0
    assert items[2].value == 3.0


def test_pi_point_snake_case_access():
    data = {
        "WebId": "P0123",
        "Name": "test",
        "PointClass": "classic",
        "PointType": "Int32",
        "EngineeringUnits": "psi",
    }
    point = PIPoint.model_validate(data)
    assert point.point_class == "classic"
    assert point.engineering_units == "psi"
