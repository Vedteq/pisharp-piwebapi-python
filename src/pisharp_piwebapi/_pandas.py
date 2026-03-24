"""Optional Pandas integration helpers for PI Web API response models.

This module is only usable when ``pandas`` is installed::

    pip install pisharp-piwebapi[pandas]

All functions raise :class:`ImportError` with an actionable message if
``pandas`` is not available, so callers get clear feedback rather than a
generic ``ModuleNotFoundError``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

    from pisharp_piwebapi.models import StreamSetItem, StreamValues


def stream_values_to_dataframe(
    values: StreamValues,
    tz: str | None = None,
) -> pd.DataFrame:
    """Convert a :class:`~pisharp_piwebapi.models.StreamValues` collection to a DataFrame.

    The returned DataFrame has a :class:`~pandas.DatetimeIndex` named
    ``"timestamp"`` and a single ``"value"`` column.  Optional quality
    columns (``"good"``, ``"questionable"``, ``"substituted"``,
    ``"annotated"``) are included only when they carry non-default data
    (i.e. when any value is ``False`` for ``good``, or ``True`` for the
    others), saving memory for callers that do not need them.

    The ``"annotated"`` column, when present, indicates values that have PI
    annotation records attached (e.g. operator comments).  It is omitted when
    no values in the result are annotated.

    Args:
        values: A :class:`~pisharp_piwebapi.models.StreamValues` instance as
            returned by ``client.streams.get_recorded()`` or
            ``client.streams.get_interpolated()``.
        tz: Optional IANA timezone name to localise the DatetimeIndex
            (e.g. ``"America/New_York"``).  When ``None`` the timestamps keep
            their original UTC-aware timezone.

    Returns:
        A :class:`~pandas.DataFrame` indexed by timestamp with at minimum a
        ``"value"`` column.

    Raises:
        ImportError: If ``pandas`` is not installed.

    Example::

        vals = client.streams.get_recorded(web_id, start_time="-1d")
        df = stream_values_to_dataframe(vals)
        print(df.head())
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "Pandas integration requires the 'pandas' extra. "
            "Install with: pip install pisharp-piwebapi[pandas]"
        ) from None

    if not values.items:
        return pd.DataFrame(
            columns=["value"],
            index=pd.DatetimeIndex([], name="timestamp"),
        )

    rows: list[dict[str, Any]] = [
        {
            "timestamp": item.timestamp,
            "value": item.value,
            "good": item.good,
            "questionable": item.questionable,
            "substituted": item.substituted,
            "annotated": item.annotated,
        }
        for item in values.items
    ]

    df = pd.DataFrame(rows).set_index("timestamp")
    df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "timestamp"

    if tz is not None:
        df.index = df.index.tz_convert(tz)

    # Drop quality columns that carry only their default values, keeping them
    # only when they convey real information (i.e. non-default data is present).
    if df["good"].all():
        df = df.drop(columns=["good"])
    if not df["questionable"].any():
        df = df.drop(columns=["questionable"])
    if not df["substituted"].any():
        df = df.drop(columns=["substituted"])
    if not df["annotated"].any():
        df = df.drop(columns=["annotated"])

    return df


def streamset_to_dataframe(
    items: list[StreamSetItem],
    tz: str | None = None,
) -> pd.DataFrame:
    """Convert a list of :class:`~pisharp_piwebapi.models.StreamSetItem` to a wide DataFrame.

    Each :class:`~pisharp_piwebapi.models.StreamSetItem` represents one stream
    (tag or AF attribute).  The resulting DataFrame has a
    :class:`~pandas.DatetimeIndex` named ``"timestamp"`` and one column per
    stream, using :attr:`~pisharp_piwebapi.models.StreamSetItem.name` as the
    column name.  Timestamps present in one stream but absent in another are
    filled with ``NaN``.

    This is particularly useful with the element-scoped and ad-hoc streamset
    methods::

        items = client.streamsets.get_recorded_by_element(elem_web_id)
        df = streamset_to_dataframe(items)

    Args:
        items: List of :class:`~pisharp_piwebapi.models.StreamSetItem` as
            returned by any ``streamsets`` method (e.g.
            ``get_recorded_by_element``, ``get_recorded_ad_hoc``).
        tz: Optional IANA timezone name to localise the DatetimeIndex
            (e.g. ``"America/New_York"``).  When ``None`` the timestamps keep
            their original UTC-aware timezone.

    Returns:
        A wide-format :class:`~pandas.DataFrame` with a
        :class:`~pandas.DatetimeIndex` and one column per stream.

    Raises:
        ImportError: If ``pandas`` is not installed.

    Example::

        items = client.streamsets.get_recorded_by_element(elem_web_id, start_time="-1d")
        df = streamset_to_dataframe(items, tz="Europe/London")
        print(df.head())
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "Pandas integration requires the 'pandas' extra. "
            "Install with: pip install pisharp-piwebapi[pandas]"
        ) from None

    if not items:
        return pd.DataFrame(index=pd.DatetimeIndex([], name="timestamp"))

    series: list[pd.Series] = []
    for item in items:
        if not item.items:
            continue
        rows: list[dict[str, Any]] = [
            {"timestamp": sv.timestamp, item.name: sv.value} for sv in item.items
        ]
        s = pd.DataFrame(rows).set_index("timestamp")[item.name]
        s.index = pd.to_datetime(s.index, utc=True)
        series.append(s)

    if not series:
        return pd.DataFrame(index=pd.DatetimeIndex([], name="timestamp"))

    df = pd.concat(series, axis=1)
    df.index.name = "timestamp"

    if tz is not None:
        df.index = df.index.tz_convert(tz)

    return df
