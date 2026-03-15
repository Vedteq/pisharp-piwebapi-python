"""Tests for the optional Pandas integration helpers."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pisharp_piwebapi._pandas import stream_values_to_dataframe
from pisharp_piwebapi.models import StreamValue, StreamValues


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
