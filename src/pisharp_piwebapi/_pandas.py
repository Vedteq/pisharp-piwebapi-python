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

    from pisharp_piwebapi.models import StreamValues


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
