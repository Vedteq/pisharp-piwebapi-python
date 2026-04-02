"""Stream read/write operations for PI Web API."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import StreamSummary, StreamUpdate, StreamValue, StreamValues

if TYPE_CHECKING:
    import httpx


class StreamsMixin:
    """Methods for reading and writing PI stream values. Mixed into the sync client class."""

    _client: httpx.Client

    def get_value(self, web_id: str) -> StreamValue:
        """Read the current (snapshot) value of a stream.

        Args:
            web_id: WebID of the PI Point or AF attribute.

        Returns:
            The current :class:`StreamValue`.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(f"/streams/{quote(web_id, safe='')}/value")
        raise_for_response(resp)
        return StreamValue.model_validate(resp.json())

    def get_recorded(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        max_count: int = 1000,
        *,
        boundary_type: str | None = None,
        filter_expression: str | None = None,
    ) -> StreamValues:
        """Read recorded (historian) values from a stream.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            start_time: Start time as a PI time string (e.g. ``"-1h"``,
                ``"2024-01-01T00:00:00Z"``). Defaults to ``"-1h"``.
            end_time: End time as a PI time string. ``"*"`` means now.
                Defaults to ``"*"``.
            max_count: Maximum number of values to return. Defaults to ``1000``.
            boundary_type: Controls how boundary events are included.
                One of ``"Inside"`` (only events strictly within the
                range), ``"Outside"`` (includes nearest events before
                start and after end), or ``"Interpolated"`` (inserts
                interpolated values at exact boundary timestamps).
                When ``None`` (default) the server uses its own default.
            filter_expression: An optional server-side filter expression.
                Only events that satisfy the expression are returned.
                Uses PI performance equation syntax, e.g.
                ``"'.' > 50"`` to return only values greater than 50.
                Defaults to ``None`` (no filtering).

        Returns:
            A :class:`StreamValues` collection containing the recorded values.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, str | int] = {
            "startTime": start_time,
            "endTime": end_time,
            "maxCount": max_count,
        }
        if boundary_type is not None:
            params["boundaryType"] = boundary_type
        if filter_expression is not None:
            params["filterExpression"] = filter_expression
        resp = self._client.get(
            f"/streams/{quote(web_id, safe='')}/recorded",
            params=params,
        )
        raise_for_response(resp)
        return StreamValues.model_validate(resp.json())

    def get_interpolated(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        interval: str = "10m",
    ) -> StreamValues:
        """Read server-side interpolated values from a stream.

        PI Web API computes values at regular intervals between ``start_time``
        and ``end_time`` using linear interpolation.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            interval: Interpolation interval (e.g. ``"10m"``, ``"1h"``).
                Defaults to ``"10m"``.

        Returns:
            A :class:`StreamValues` collection containing the interpolated values.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/streams/{quote(web_id, safe='')}/interpolated",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "interval": interval,
            },
        )
        raise_for_response(resp)
        return StreamValues.model_validate(resp.json())

    def get_summary(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        summary_type: str = "All",
        calculation_basis: str = "TimeWeighted",
    ) -> StreamSummary:
        """Read summary statistics for a stream over a time range.

        Calls ``GET /streams/{webId}/summary`` and returns the summary
        statistics (minimum, maximum, mean, standard deviation, count, and
        percent-good) computed by the PI server.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            start_time: Start time as a PI time string (e.g. ``"-8h"``,
                ``"2024-01-01T00:00:00Z"``). Defaults to ``"-1h"``.
            end_time: End time as a PI time string. ``"*"`` means now.
                Defaults to ``"*"``.
            summary_type: Comma-separated list of summary types to request.
                Valid values are ``"All"``, ``"Total"``, ``"Average"``,
                ``"Minimum"``, ``"Maximum"``, ``"Range"``, ``"StdDev"``,
                ``"PopulationStdDev"``, ``"Count"``, ``"PercentGood"``.
                Defaults to ``"All"``.
            calculation_basis: How values are weighted when computing the
                summary. One of ``"TimeWeighted"`` (default) or
                ``"EventWeighted"``.

        Returns:
            A :class:`StreamSummary` whose ``items`` list contains one
            :class:`StreamSummaryValue` per statistic type requested.
            Use :meth:`StreamSummary.as_dict` for a compact ``{type: value}``
            view.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/streams/{quote(web_id, safe='')}/summary",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "summaryType": summary_type,
                "calculationBasis": calculation_basis,
            },
        )
        raise_for_response(resp)
        return StreamSummary.model_validate(resp.json())

    def get_end(self, web_id: str) -> StreamValue:
        """Read the end-of-stream (last archived) value.

        Unlike :meth:`get_value` which returns the current snapshot,
        ``get_end`` returns the most recent event stored in the archive.
        This is useful when the snapshot may have been overwritten by an
        out-of-order event.

        Calls ``GET /streams/{webId}/end``.

        Args:
            web_id: WebID of the PI Point or AF attribute.

        Returns:
            The last archived :class:`StreamValue`.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(f"/streams/{quote(web_id, safe='')}/end")
        raise_for_response(resp)
        return StreamValue.model_validate(resp.json())

    def get_plot(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        intervals: int = 24,
    ) -> StreamValues:
        """Read plot-optimized values from a stream.

        The PI server selects the most visually interesting values (peaks,
        valleys, step changes) within each interval, producing data ideal
        for trend charts.  This is the same algorithm used by PI Vision.

        Calls ``GET /streams/{webId}/plot``.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            intervals: Number of intervals to divide the time range into.
                The server returns up to ~5 values per interval.
                Defaults to ``24``.

        Returns:
            A :class:`StreamValues` collection containing the plot values.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/streams/{quote(web_id, safe='')}/plot",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "intervals": intervals,
            },
        )
        raise_for_response(resp)
        return StreamValues.model_validate(resp.json())

    def get_recorded_at_time(
        self,
        web_id: str,
        time: str,
        retrieval_mode: str = "Auto",
    ) -> StreamValue:
        """Read a single recorded value at (or near) a specific time.

        Calls ``GET /streams/{webId}/recordedattime``.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            time: The timestamp to retrieve a value for, as a PI time
                string (e.g. ``"2024-06-01T12:00:00Z"``, ``"*-1h"``).
            retrieval_mode: How to select the value relative to *time*.
                One of ``"Auto"`` (default), ``"AtOrBefore"``,
                ``"Before"``, ``"AtOrAfter"``, ``"After"``, or
                ``"Exact"``.

        Returns:
            A single :class:`StreamValue` at the requested time.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/streams/{quote(web_id, safe='')}/recordedattime",
            params={"time": time, "retrievalMode": retrieval_mode},
        )
        raise_for_response(resp)
        return StreamValue.model_validate(resp.json())

    def get_recorded_at_times(
        self,
        web_id: str,
        times: list[str],
        retrieval_mode: str = "Auto",
    ) -> StreamValues:
        """Read recorded values at multiple specific times.

        Calls ``GET /streams/{webId}/recordedattimes``.  The server
        returns one value per requested timestamp, selected according
        to *retrieval_mode*.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            times: List of PI time strings (e.g.
                ``["2024-06-01T11:00:00Z", "2024-06-01T12:00:00Z"]``).
            retrieval_mode: How to select values relative to each time.
                Defaults to ``"Auto"``.

        Returns:
            A :class:`StreamValues` collection with one value per
            requested time.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: list[tuple[str, str | int | float | bool | None]] = [
            ("retrievalMode", retrieval_mode),
        ]
        for t in times:
            params.append(("time", t))
        resp = self._client.get(
            f"/streams/{quote(web_id, safe='')}/recordedattimes",
            params=params,
        )
        raise_for_response(resp)
        return StreamValues.model_validate(resp.json())

    def get_interpolated_at_times(
        self,
        web_id: str,
        times: list[str],
    ) -> StreamValues:
        """Read interpolated values at specific times.

        Calls ``GET /streams/{webId}/interpolatedattimes``.  The server
        computes an interpolated value at each requested timestamp.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            times: List of PI time strings (e.g.
                ``["2024-06-01T11:00:00Z", "2024-06-01T12:00:00Z"]``).

        Returns:
            A :class:`StreamValues` collection with one interpolated
            value per requested time.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: list[tuple[str, str | int | float | bool | None]] = [
            ("time", t) for t in times
        ]
        resp = self._client.get(
            f"/streams/{quote(web_id, safe='')}/interpolatedattimes",
            params=params,
        )
        raise_for_response(resp)
        return StreamValues.model_validate(resp.json())

    def update_value(
        self,
        web_id: str,
        value: Any,
        timestamp: str | datetime | None = None,
    ) -> None:
        """Write a single value to a stream.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            value: The value to write. Must be compatible with the point's type.
            timestamp: Optional timestamp. Accepts a :class:`datetime` instance
                (serialized to ISO 8601) or a PI time string such as
                ``"2024-06-01T12:00:00Z"``. If omitted the server uses the
                current time.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = {"Value": value}
        if timestamp is not None:
            body["Timestamp"] = (
                timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
            )
        resp = self._client.post(
            f"/streams/{quote(web_id, safe='')}/value",
            json=body,
        )
        raise_for_response(resp)

    def update_values(
        self,
        web_id: str,
        values: list[dict[str, Any]],
    ) -> None:
        """Write multiple values to a stream in a single request.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            values: List of value dicts, each with a ``"Value"`` key and
                optionally a ``"Timestamp"`` key (ISO 8601 string).

                Example::

                    [
                        {"Value": 1.0, "Timestamp": "2024-06-01T10:00:00Z"},
                        {"Value": 2.0, "Timestamp": "2024-06-01T11:00:00Z"},
                    ]

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.post(
            f"/streams/{quote(web_id, safe='')}/recorded",
            json=values,
        )
        raise_for_response(resp)

    def register_stream_update(
        self,
        web_id: str,
    ) -> StreamUpdate:
        """Register for incremental stream updates (marker-based).

        Calls ``POST /streams/{webId}/updates`` to start tracking
        changes on the given stream.  The returned :class:`StreamUpdate`
        contains a ``latest_marker`` that must be passed to
        :meth:`retrieve_stream_update` to fetch subsequent changes.

        This is a lightweight alternative to WebSocket channels for
        polling-based integrations.

        Args:
            web_id: WebID of the PI Point or AF attribute to track.

        Returns:
            A :class:`StreamUpdate` with the initial marker and any
            events available at registration time.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.post(
            f"/streams/{quote(web_id, safe='')}/updates",
        )
        raise_for_response(resp)
        return StreamUpdate.model_validate(resp.json())

    def retrieve_stream_update(
        self,
        marker: str,
    ) -> StreamUpdate:
        """Retrieve incremental updates since a previous marker.

        Calls ``GET /streams/updates/{marker}`` to fetch new events
        that have occurred since the marker was issued.  The returned
        :class:`StreamUpdate` contains a new ``latest_marker`` for
        chaining subsequent calls.

        Typical usage::

            update = client.streams.register_stream_update(web_id)
            marker = update.latest_marker
            # ... wait ...
            update = client.streams.retrieve_stream_update(marker)
            for event in update.events:
                process(event)
            marker = update.latest_marker  # use for next call

        Args:
            marker: The marker string from a previous
                :meth:`register_stream_update` or
                :meth:`retrieve_stream_update` call.

        Returns:
            A :class:`StreamUpdate` with new events and an updated
            marker.

        Raises:
            PIWebAPIError: If the marker is invalid or expired.
        """
        validate_web_id(marker, "marker")
        resp = self._client.get(
            f"/streams/updates/{quote(marker, safe='')}",
        )
        raise_for_response(resp)
        return StreamUpdate.model_validate(resp.json())


class AsyncStreamsMixin:
    """Async methods for reading and writing PI stream values. Mixed into the async client class."""

    _client: httpx.AsyncClient

    async def get_value(self, web_id: str) -> StreamValue:
        """Read the current (snapshot) value of a stream.

        Args:
            web_id: WebID of the PI Point or AF attribute.

        Returns:
            The current :class:`StreamValue`.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(f"/streams/{quote(web_id, safe='')}/value")
        await raise_for_response_async(resp)
        return StreamValue.model_validate(resp.json())

    async def get_recorded(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        max_count: int = 1000,
        *,
        boundary_type: str | None = None,
        filter_expression: str | None = None,
    ) -> StreamValues:
        """Read recorded (historian) values from a stream.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            max_count: Maximum number of values to return. Defaults to ``1000``.
            boundary_type: Controls how boundary events are included.
                One of ``"Inside"``, ``"Outside"``, or
                ``"Interpolated"``.  When ``None`` (default) the server
                uses its own default.
            filter_expression: An optional server-side filter expression.
                Only events that satisfy the expression are returned.
                Uses PI performance equation syntax, e.g.
                ``"'.' > 50"`` to return only values greater than 50.
                Defaults to ``None`` (no filtering).

        Returns:
            A :class:`StreamValues` collection containing the recorded values.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, str | int] = {
            "startTime": start_time,
            "endTime": end_time,
            "maxCount": max_count,
        }
        if boundary_type is not None:
            params["boundaryType"] = boundary_type
        if filter_expression is not None:
            params["filterExpression"] = filter_expression
        resp = await self._client.get(
            f"/streams/{quote(web_id, safe='')}/recorded",
            params=params,
        )
        await raise_for_response_async(resp)
        return StreamValues.model_validate(resp.json())

    async def get_interpolated(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        interval: str = "10m",
    ) -> StreamValues:
        """Read server-side interpolated values from a stream.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            interval: Interpolation interval (e.g. ``"10m"``, ``"1h"``).
                Defaults to ``"10m"``.

        Returns:
            A :class:`StreamValues` collection containing the interpolated values.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/streams/{quote(web_id, safe='')}/interpolated",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "interval": interval,
            },
        )
        await raise_for_response_async(resp)
        return StreamValues.model_validate(resp.json())

    async def get_summary(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        summary_type: str = "All",
        calculation_basis: str = "TimeWeighted",
    ) -> StreamSummary:
        """Read summary statistics for a stream over a time range.

        Calls ``GET /streams/{webId}/summary`` and returns the summary
        statistics computed by the PI server.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            summary_type: Comma-separated list of summary types to request.
                Defaults to ``"All"``.
            calculation_basis: ``"TimeWeighted"`` (default) or
                ``"EventWeighted"``.

        Returns:
            A :class:`StreamSummary` whose ``items`` list contains one
            :class:`StreamSummaryValue` per statistic type requested.
            Use :meth:`StreamSummary.as_dict` for a compact ``{type: value}``
            view.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/streams/{quote(web_id, safe='')}/summary",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "summaryType": summary_type,
                "calculationBasis": calculation_basis,
            },
        )
        await raise_for_response_async(resp)
        return StreamSummary.model_validate(resp.json())

    async def get_end(self, web_id: str) -> StreamValue:
        """Read the end-of-stream (last archived) value.

        Unlike :meth:`get_value` which returns the current snapshot,
        ``get_end`` returns the most recent event stored in the archive.

        Calls ``GET /streams/{webId}/end``.

        Args:
            web_id: WebID of the PI Point or AF attribute.

        Returns:
            The last archived :class:`StreamValue`.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/streams/{quote(web_id, safe='')}/end"
        )
        await raise_for_response_async(resp)
        return StreamValue.model_validate(resp.json())

    async def get_plot(
        self,
        web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        intervals: int = 24,
    ) -> StreamValues:
        """Read plot-optimized values from a stream.

        The PI server selects the most visually interesting values (peaks,
        valleys, step changes) within each interval, producing data ideal
        for trend charts.  This is the same algorithm used by PI Vision.

        Calls ``GET /streams/{webId}/plot``.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            intervals: Number of intervals to divide the time range into.
                The server returns up to ~5 values per interval.
                Defaults to ``24``.

        Returns:
            A :class:`StreamValues` collection containing the plot values.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/streams/{quote(web_id, safe='')}/plot",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "intervals": intervals,
            },
        )
        await raise_for_response_async(resp)
        return StreamValues.model_validate(resp.json())

    async def get_recorded_at_time(
        self,
        web_id: str,
        time: str,
        retrieval_mode: str = "Auto",
    ) -> StreamValue:
        """Read a single recorded value at (or near) a specific time.

        Calls ``GET /streams/{webId}/recordedattime``.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            time: The timestamp to retrieve a value for, as a PI time
                string (e.g. ``"2024-06-01T12:00:00Z"``, ``"*-1h"``).
            retrieval_mode: How to select the value relative to *time*.
                One of ``"Auto"`` (default), ``"AtOrBefore"``,
                ``"Before"``, ``"AtOrAfter"``, ``"After"``, or
                ``"Exact"``.

        Returns:
            A single :class:`StreamValue` at the requested time.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/streams/{quote(web_id, safe='')}/recordedattime",
            params={"time": time, "retrievalMode": retrieval_mode},
        )
        await raise_for_response_async(resp)
        return StreamValue.model_validate(resp.json())

    async def get_recorded_at_times(
        self,
        web_id: str,
        times: list[str],
        retrieval_mode: str = "Auto",
    ) -> StreamValues:
        """Read recorded values at multiple specific times.

        Calls ``GET /streams/{webId}/recordedattimes``.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            times: List of PI time strings.
            retrieval_mode: How to select values relative to each time.
                Defaults to ``"Auto"``.

        Returns:
            A :class:`StreamValues` collection with one value per
            requested time.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: list[tuple[str, str | int | float | bool | None]] = [
            ("retrievalMode", retrieval_mode),
        ]
        for t in times:
            params.append(("time", t))
        resp = await self._client.get(
            f"/streams/{quote(web_id, safe='')}/recordedattimes",
            params=params,
        )
        await raise_for_response_async(resp)
        return StreamValues.model_validate(resp.json())

    async def get_interpolated_at_times(
        self,
        web_id: str,
        times: list[str],
    ) -> StreamValues:
        """Read interpolated values at specific times.

        Calls ``GET /streams/{webId}/interpolatedattimes``.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            times: List of PI time strings.

        Returns:
            A :class:`StreamValues` collection with one interpolated
            value per requested time.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: list[tuple[str, str | int | float | bool | None]] = [
            ("time", t) for t in times
        ]
        resp = await self._client.get(
            f"/streams/{quote(web_id, safe='')}/interpolatedattimes",
            params=params,
        )
        await raise_for_response_async(resp)
        return StreamValues.model_validate(resp.json())

    async def update_value(
        self,
        web_id: str,
        value: Any,
        timestamp: str | datetime | None = None,
    ) -> None:
        """Write a single value to a stream.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            value: The value to write.
            timestamp: Optional timestamp as a :class:`datetime` or PI time string.
                If omitted the server uses the current time.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = {"Value": value}
        if timestamp is not None:
            body["Timestamp"] = (
                timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
            )
        resp = await self._client.post(
            f"/streams/{quote(web_id, safe='')}/value",
            json=body,
        )
        await raise_for_response_async(resp)

    async def update_values(
        self,
        web_id: str,
        values: list[dict[str, Any]],
    ) -> None:
        """Write multiple values to a stream in a single request.

        Args:
            web_id: WebID of the PI Point or AF attribute.
            values: List of value dicts, each with a ``"Value"`` key and
                optionally a ``"Timestamp"`` key (ISO 8601 string).

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.post(
            f"/streams/{quote(web_id, safe='')}/recorded",
            json=values,
        )
        await raise_for_response_async(resp)

    async def register_stream_update(
        self,
        web_id: str,
    ) -> StreamUpdate:
        """Register for incremental stream updates (marker-based).

        Calls ``POST /streams/{webId}/updates`` to start tracking
        changes on the given stream.

        Args:
            web_id: WebID of the PI Point or AF attribute to track.

        Returns:
            A :class:`StreamUpdate` with the initial marker and any
            events available at registration time.

        Raises:
            NotFoundError: If no stream with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.post(
            f"/streams/{quote(web_id, safe='')}/updates",
        )
        await raise_for_response_async(resp)
        return StreamUpdate.model_validate(resp.json())

    async def retrieve_stream_update(
        self,
        marker: str,
    ) -> StreamUpdate:
        """Retrieve incremental updates since a previous marker.

        Calls ``GET /streams/updates/{marker}``.

        Args:
            marker: The marker string from a previous
                :meth:`register_stream_update` or
                :meth:`retrieve_stream_update` call.

        Returns:
            A :class:`StreamUpdate` with new events and an updated
            marker.

        Raises:
            PIWebAPIError: If the marker is invalid or expired.
        """
        resp = await self._client.get(
            f"/streams/updates/{quote(marker, safe='')}",
        )
        await raise_for_response_async(resp)
        return StreamUpdate.model_validate(resp.json())
