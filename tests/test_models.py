"""Tests for Pydantic response models."""

from datetime import datetime

from pisharp_piwebapi.models import PIPoint, StreamSetItem, StreamValue, StreamValues


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


def test_stream_value_null_timestamp():
    """StreamValue accepts null Timestamp (e.g. Count/PercentGood summaries)."""
    data = {
        "Timestamp": None,
        "Value": 42,
        "Good": True,
    }
    value = StreamValue.model_validate(data)
    assert value.timestamp is None
    assert value.value == 42


def test_stream_value_missing_timestamp():
    """StreamValue works when Timestamp key is absent."""
    data = {"Value": 99, "Good": True}
    value = StreamValue.model_validate(data)
    assert value.timestamp is None
    assert value.value == 99


def test_stream_value_identity_fields():
    """StreamValue captures WebId, Name, Path from streamset snapshot responses."""
    data = {
        "WebId": "P0abc",
        "Name": "sinusoid",
        "Path": "\\\\SERVER\\sinusoid",
        "Timestamp": "2024-06-01T12:00:00Z",
        "Value": 3.14,
        "Good": True,
    }
    value = StreamValue.model_validate(data)
    assert value.web_id == "P0abc"
    assert value.name == "sinusoid"
    assert value.path == "\\\\SERVER\\sinusoid"


def test_stream_set_item_errors_field():
    """StreamSetItem exposes Errors for partial-failure detection."""
    data = {
        "WebId": "P0bad",
        "Name": "deleted_tag",
        "Path": "",
        "Items": [],
        "Errors": ["PI Point not found."],
        "Links": {},
    }
    item = StreamSetItem.model_validate(data)
    assert len(item.errors) == 1
    assert "not found" in item.errors[0]
    assert len(item.items) == 0


def test_stream_set_item_no_errors_by_default():
    """StreamSetItem.errors defaults to empty list."""
    data = {
        "WebId": "P0ok",
        "Name": "good_tag",
        "Items": [
            {"Timestamp": "2024-06-01T12:00:00Z", "Value": 1.0, "Good": True},
        ],
    }
    item = StreamSetItem.model_validate(data)
    assert item.errors == []
    assert len(item.items) == 1
