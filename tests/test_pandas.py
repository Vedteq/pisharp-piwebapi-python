"""Tests for pandas integration (StreamValues.to_dataframe)."""

from __future__ import annotations

import pandas as pd

from pisharp_piwebapi.models import StreamValues


def test_to_dataframe_basic():
    data = {
        "WebId": "S0123",
        "Name": "sinusoid",
        "Items": [
            {"Timestamp": "2024-06-15T10:00:00Z", "Value": 1.0, "Good": True},
            {"Timestamp": "2024-06-15T10:05:00Z", "Value": 2.0, "Good": True},
            {"Timestamp": "2024-06-15T10:10:00Z", "Value": 3.0, "Good": False},
        ],
    }
    values = StreamValues.model_validate(data)
    df = values.to_dataframe()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert df.index.name == "timestamp"
    assert list(df["value"]) == [1.0, 2.0, 3.0]
    assert list(df["good"]) == [True, True, False]


def test_to_dataframe_empty():
    data = {"WebId": "S0123", "Name": "empty", "Items": []}
    values = StreamValues.model_validate(data)
    df = values.to_dataframe()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0


def test_to_dataframe_preserves_all_columns():
    data = {
        "Items": [
            {
                "Timestamp": "2024-06-15T10:00:00Z",
                "Value": 42.5,
                "Good": True,
                "Questionable": True,
                "Substituted": False,
                "Annotated": True,
                "UnitsAbbreviation": "degC",
            },
        ],
    }
    values = StreamValues.model_validate(data)
    df = values.to_dataframe()

    assert df.iloc[0]["value"] == 42.5
    assert df.iloc[0]["questionable"] == True  # noqa: E712
    assert df.iloc[0]["annotated"] == True  # noqa: E712
    assert df.iloc[0]["units_abbreviation"] == "degC"
