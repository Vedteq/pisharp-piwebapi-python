"""Tests for the optional Pandas integration helpers."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pisharp_piwebapi._pandas import stream_values_to_dataframe, streamset_to_dataframe
from pisharp_piwebapi.models import StreamSetItem, StreamValue, StreamValues


def _make_stream_values(
    entries: list[tuple[str, float]],
    *,
    good: bool = True,
) -> StreamValues:
    """Build a StreamValues fixture from (iso_timestamp, float) pairs."""
    items = [
        StreamValue(
            Timestamp=ts,
            Value=val,
            Good=good,
            Questionable=False,
            Substituted=False,
            UnitsAbbreviation="degC",
            Annotated=False,
        )
        for ts, val in entries
    ]
    return StreamValues(Items=items, WebId="F1AbTest", Name="sinusoid", Path="", Links={})


# ===========================================================================
# Happy path — single value
# ===========================================================================


def test_single_value_produces_one_row() -> None:
    """A StreamValues with one item produces a one-row DataFrame."""
    pandas = pytest.importorskip("pandas")

    vals = _make_stream_values([("2024-06-01T12:00:00Z", 3.14)])
    df = stream_values_to_dataframe(vals)

    assert len(df) == 1
    assert "value" in df.columns
    assert df["value"].iloc[0] == pytest.approx(3.14)


# ===========================================================================
# Happy path — multiple values, default quality columns dropped
# ===========================================================================


def test_multiple_values_all_good_drops_quality_columns() -> None:
    """When all values are good/not-questionable/not-substituted the quality columns are omitted."""
    pytest.importorskip("pandas")

    vals = _make_stream_values([
        ("2024-06-01T10:00:00Z", 1.0),
        ("2024-06-01T11:00:00Z", 2.0),
        ("2024-06-01T12:00:00Z", 3.0),
    ])
    df = stream_values_to_dataframe(vals)

    assert list(df.columns) == ["value"]
    assert len(df) == 3
    assert df["value"].tolist() == pytest.approx([1.0, 2.0, 3.0])


# ===========================================================================
# Happy path — bad-quality values retain "good" column
# ===========================================================================


def test_bad_quality_retains_good_column() -> None:
    """When any value is not good, the 'good' column is kept in the output."""
    pytest.importorskip("pandas")

    items = [
        StreamValue(
            Timestamp="2024-06-01T10:00:00Z",
            Value=1.0,
            Good=False,
            Questionable=False,
            Substituted=False,
            UnitsAbbreviation="",
            Annotated=False,
        ),
        StreamValue(
            Timestamp="2024-06-01T11:00:00Z",
            Value=2.0,
            Good=True,
            Questionable=False,
            Substituted=False,
            UnitsAbbreviation="",
            Annotated=False,
        ),
    ]
    vals = StreamValues(Items=items, WebId="F1", Name="tag", Path="", Links={})
    df = stream_values_to_dataframe(vals)

    assert "good" in df.columns
    assert df["good"].tolist() == [False, True]


# ===========================================================================
# Happy path — index is UTC-aware DatetimeIndex
# ===========================================================================


def test_index_is_utc_aware() -> None:
    """The DataFrame index must be a UTC-aware DatetimeIndex."""
    pandas = pytest.importorskip("pandas")

    vals = _make_stream_values([("2024-06-01T12:00:00Z", 0.0)])
    df = stream_values_to_dataframe(vals)

    assert isinstance(df.index, pandas.DatetimeIndex)
    assert df.index.name == "timestamp"
    assert str(df.index.tz) == "UTC"


# ===========================================================================
# Happy path — timezone conversion
# ===========================================================================


def test_tz_conversion() -> None:
    """Passing tz= converts the DatetimeIndex to the given timezone."""
    pandas = pytest.importorskip("pandas")

    vals = _make_stream_values([("2024-06-01T12:00:00Z", 1.0)])
    df = stream_values_to_dataframe(vals, tz="America/New_York")

    assert str(df.index.tz) == "America/New_York"
    # 12:00 UTC = 08:00 EDT (UTC-4 in June)
    assert df.index[0].hour == 8


# ===========================================================================
# Edge case — empty StreamValues
# ===========================================================================


def test_empty_stream_values_returns_empty_dataframe() -> None:
    """An empty StreamValues produces an empty DataFrame with a 'value' column."""
    pandas = pytest.importorskip("pandas")

    vals = StreamValues(Items=[], WebId="F1", Name="tag", Path="", Links={})
    df = stream_values_to_dataframe(vals)

    assert len(df) == 0
    assert "value" in df.columns
    assert isinstance(df.index, pandas.DatetimeIndex)
    assert df.index.name == "timestamp"


# ===========================================================================
# Edge case — datetime objects (not just strings) as timestamps
# ===========================================================================


def test_datetime_objects_as_timestamps() -> None:
    """StreamValue timestamps that are already datetime objects are handled correctly."""
    pytest.importorskip("pandas")

    item = StreamValue(
        Timestamp=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        Value=7.77,
        Good=True,
        Questionable=False,
        Substituted=False,
        UnitsAbbreviation="",
        Annotated=False,
    )
    vals = StreamValues(Items=[item], WebId="F1", Name="tag", Path="", Links={})
    df = stream_values_to_dataframe(vals)

    assert df["value"].iloc[0] == pytest.approx(7.77)


# ===========================================================================
# Happy path — annotated column retained when at least one value is annotated
# ===========================================================================


def test_annotated_column_retained_when_present() -> None:
    """When any value is annotated, the 'annotated' column is kept in the output."""
    pytest.importorskip("pandas")

    items = [
        StreamValue(
            Timestamp="2024-06-01T10:00:00Z",
            Value=1.0,
            Good=True,
            Questionable=False,
            Substituted=False,
            UnitsAbbreviation="",
            Annotated=True,  # This one has an annotation attached
        ),
        StreamValue(
            Timestamp="2024-06-01T11:00:00Z",
            Value=2.0,
            Good=True,
            Questionable=False,
            Substituted=False,
            UnitsAbbreviation="",
            Annotated=False,
        ),
    ]
    vals = StreamValues(Items=items, WebId="F1", Name="tag", Path="", Links={})
    df = stream_values_to_dataframe(vals)

    assert "annotated" in df.columns
    assert df["annotated"].tolist() == [True, False]


def test_annotated_column_dropped_when_all_false() -> None:
    """When no values are annotated, the 'annotated' column is omitted."""
    pytest.importorskip("pandas")

    vals = _make_stream_values([
        ("2024-06-01T10:00:00Z", 1.0),
        ("2024-06-01T11:00:00Z", 2.0),
    ])
    df = stream_values_to_dataframe(vals)

    assert "annotated" not in df.columns


# ===========================================================================
# Error case — missing pandas raises ImportError with helpful message
# ===========================================================================


def test_import_error_message_is_actionable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulating missing pandas gives an ImportError with install instructions."""
    import builtins

    real_import = builtins.__import__

    def _mock_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "pandas":
            raise ImportError("No module named 'pandas'")
        return real_import(name, *args, **kwargs)

    vals = StreamValues(Items=[], WebId="F1", Name="tag", Path="", Links={})

    monkeypatch.setattr(builtins, "__import__", _mock_import)
    with pytest.raises(ImportError, match="pip install pisharp-piwebapi\\[pandas\\]"):
        stream_values_to_dataframe(vals)


# ===========================================================================
# StreamValues.to_dataframe() method tests
# ===========================================================================


def test_to_dataframe_basic() -> None:
    """StreamValues.to_dataframe() produces a valid DataFrame."""
    pandas = pytest.importorskip("pandas")

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

    assert isinstance(df, pandas.DataFrame)
    assert len(df) == 3
    assert df.index.name == "timestamp"
    assert list(df["value"]) == [1.0, 2.0, 3.0]
    assert list(df["good"]) == [True, True, False]


def test_to_dataframe_empty() -> None:
    """StreamValues.to_dataframe() on empty items produces an empty DataFrame."""
    pandas = pytest.importorskip("pandas")

    data = {"WebId": "S0123", "Name": "empty", "Items": []}
    values = StreamValues.model_validate(data)
    df = values.to_dataframe()

    assert isinstance(df, pandas.DataFrame)
    assert len(df) == 0


def test_to_dataframe_preserves_all_columns() -> None:
    """StreamValues.to_dataframe() preserves all quality and unit columns."""
    pytest.importorskip("pandas")

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


# ===========================================================================
# streamset_to_dataframe tests
# ===========================================================================


def _make_stream_set_item(name: str, web_id: str, entries: list[tuple[str, float]]) -> StreamSetItem:
    """Build a StreamSetItem fixture from a name and (iso_timestamp, value) pairs."""
    sv_items = [
        StreamValue(
            Timestamp=ts,
            Value=val,
            Good=True,
            Questionable=False,
            Substituted=False,
            UnitsAbbreviation="",
            Annotated=False,
        )
        for ts, val in entries
    ]
    return StreamSetItem(WebId=web_id, Name=name, Path="", Items=sv_items, Links={})


def test_streamset_to_dataframe_basic_wide_format() -> None:
    """streamset_to_dataframe produces a wide DataFrame with one column per tag."""
    pandas = pytest.importorskip("pandas")

    items = [
        _make_stream_set_item(
            "sinusoid",
            "W1",
            [("2024-06-01T11:00:00Z", 1.0), ("2024-06-01T12:00:00Z", 2.0)],
        ),
        _make_stream_set_item(
            "cdt158",
            "W2",
            [("2024-06-01T11:00:00Z", 10.0), ("2024-06-01T12:00:00Z", 20.0)],
        ),
    ]
    df = streamset_to_dataframe(items)

    assert isinstance(df, pandas.DataFrame)
    assert "sinusoid" in df.columns
    assert "cdt158" in df.columns
    assert len(df) == 2
    assert df["sinusoid"].tolist() == pytest.approx([1.0, 2.0])
    assert df["cdt158"].tolist() == pytest.approx([10.0, 20.0])


def test_streamset_to_dataframe_index_is_utc_datetimeindex() -> None:
    """streamset_to_dataframe produces a UTC-aware DatetimeIndex named 'timestamp'."""
    pandas = pytest.importorskip("pandas")

    items = [
        _make_stream_set_item("tag1", "W1", [("2024-06-01T12:00:00Z", 42.0)]),
    ]
    df = streamset_to_dataframe(items)

    assert isinstance(df.index, pandas.DatetimeIndex)
    assert df.index.name == "timestamp"
    assert str(df.index.tz) == "UTC"


def test_streamset_to_dataframe_tz_conversion() -> None:
    """streamset_to_dataframe converts the index to the requested timezone."""
    pytest.importorskip("pandas")

    items = [
        _make_stream_set_item("tag1", "W1", [("2024-06-01T12:00:00Z", 1.0)]),
    ]
    df = streamset_to_dataframe(items, tz="America/New_York")

    assert str(df.index.tz) == "America/New_York"
    # 12:00 UTC = 08:00 EDT (UTC-4 in June)
    assert df.index[0].hour == 8


def test_streamset_to_dataframe_misaligned_timestamps_filled_with_nan() -> None:
    """When two streams have different timestamps, missing values appear as NaN."""
    pandas = pytest.importorskip("pandas")

    items = [
        _make_stream_set_item("tagA", "W1", [("2024-06-01T11:00:00Z", 1.0)]),
        _make_stream_set_item("tagB", "W2", [("2024-06-01T12:00:00Z", 2.0)]),
    ]
    df = streamset_to_dataframe(items)

    # Two distinct timestamps → two rows, each stream missing one value
    assert len(df) == 2
    assert pandas.isna(df.loc[df.index[0], "tagB"])
    assert pandas.isna(df.loc[df.index[1], "tagA"])


def test_streamset_to_dataframe_empty_list_returns_empty_dataframe() -> None:
    """An empty items list returns an empty DataFrame with a DatetimeIndex."""
    pandas = pytest.importorskip("pandas")

    df = streamset_to_dataframe([])

    assert isinstance(df, pandas.DataFrame)
    assert len(df) == 0
    assert isinstance(df.index, pandas.DatetimeIndex)
    assert df.index.name == "timestamp"


def test_streamset_to_dataframe_items_with_no_values_skipped() -> None:
    """StreamSetItems with empty items lists are silently skipped."""
    pandas = pytest.importorskip("pandas")

    item_with_data = _make_stream_set_item("tagA", "W1", [("2024-06-01T12:00:00Z", 5.0)])
    empty_item = StreamSetItem(WebId="W2", Name="tagB", Path="", Items=[], Links={})
    df = streamset_to_dataframe([item_with_data, empty_item])

    assert "tagA" in df.columns
    assert "tagB" not in df.columns
    assert len(df) == 1


def test_streamset_to_dataframe_import_error_is_actionable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulating missing pandas gives an ImportError with install instructions."""
    import builtins

    real_import = builtins.__import__

    def _mock_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "pandas":
            raise ImportError("No module named 'pandas'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _mock_import)
    with pytest.raises(ImportError, match="pip install pisharp-piwebapi\\[pandas\\]"):
        streamset_to_dataframe([])
