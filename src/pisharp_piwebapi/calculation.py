"""Server-side calculation (expression evaluation) for PI Web API.

The ``/calculation`` endpoints let you evaluate PI performance-equation
expressions on the server without downloading raw values first.  This is
especially useful for derived calculations, cross-tag arithmetic, and
on-the-fly aggregations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import StreamSummary, StreamValues

if TYPE_CHECKING:
    from collections.abc import Sequence

    import httpx


class CalculationMixin:
    """Methods for server-side expression evaluation via ``/calculation``.

    Mixed into the sync client class.
    """

    _client: httpx.Client

    def get_recorded(
        self,
        expression: str,
        start_time: str = "-1h",
        end_time: str = "*",
        *,
        web_id: str | None = None,
    ) -> StreamValues:
        """Evaluate an expression at the recorded event times of its inputs.

        Calls ``GET /calculation/recorded``.

        Args:
            expression: A PI performance equation expression, e.g.
                ``"'sinusoid' * 2 + 10"``.
            start_time: Start time as a PI time string. Defaults to
                ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"``
                (now).
            web_id: Optional WebID of a target PI Point or AF attribute
                to provide context for relative tag references in the
                expression (e.g. ``'.'``).

        Returns:
            A :class:`StreamValues` collection of calculated values.

        Raises:
            PIWebAPIError: If the expression is invalid or the server
                returns a non-2xx response.
        """
        params: dict[str, str] = {
            "expression": expression,
            "startTime": start_time,
            "endTime": end_time,
        }
        if web_id is not None:
            validate_web_id(web_id, "web_id")
            params["webId"] = web_id
        resp = self._client.get("/calculation/recorded", params=params)
        raise_for_response(resp)
        return StreamValues.model_validate(resp.json())

    def get_summary(
        self,
        expression: str,
        start_time: str = "-1h",
        end_time: str = "*",
        summary_type: str = "All",
        calculation_basis: str = "TimeWeighted",
        *,
        web_id: str | None = None,
    ) -> StreamSummary:
        """Compute summary statistics of an expression over a time range.

        Calls ``GET /calculation/summary``.

        Args:
            expression: A PI performance equation expression.
            start_time: Start time as a PI time string. Defaults to
                ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"``
                (now).
            summary_type: Comma-separated list of summary types.
                Defaults to ``"All"``.
            calculation_basis: ``"TimeWeighted"`` (default) or
                ``"EventWeighted"``.
            web_id: Optional context WebID for relative tag references.

        Returns:
            A :class:`StreamSummary` with the requested statistics.

        Raises:
            PIWebAPIError: If the expression is invalid or the server
                returns a non-2xx response.
        """
        params: dict[str, str] = {
            "expression": expression,
            "startTime": start_time,
            "endTime": end_time,
            "summaryType": summary_type,
            "calculationBasis": calculation_basis,
        }
        if web_id is not None:
            validate_web_id(web_id, "web_id")
            params["webId"] = web_id
        resp = self._client.get("/calculation/summary", params=params)
        raise_for_response(resp)
        return StreamSummary.model_validate(resp.json())

    def get_at_intervals(
        self,
        expression: str,
        start_time: str = "-1h",
        end_time: str = "*",
        sample_interval: str = "10m",
        *,
        web_id: str | None = None,
    ) -> StreamValues:
        """Evaluate an expression at regular time intervals.

        Calls ``GET /calculation/intervals``.  PI Web API evaluates
        the expression at each step between ``start_time`` and
        ``end_time``, spaced by ``sample_interval``.

        Args:
            expression: A PI performance equation expression.
            start_time: Start time as a PI time string. Defaults to
                ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"``
                (now).
            sample_interval: Evaluation interval (e.g. ``"10m"``,
                ``"1h"``). Defaults to ``"10m"``.
            web_id: Optional context WebID for relative tag references.

        Returns:
            A :class:`StreamValues` collection of calculated values.

        Raises:
            PIWebAPIError: If the expression is invalid or the server
                returns a non-2xx response.
        """
        params: dict[str, str] = {
            "expression": expression,
            "startTime": start_time,
            "endTime": end_time,
            "sampleInterval": sample_interval,
        }
        if web_id is not None:
            validate_web_id(web_id, "web_id")
            params["webId"] = web_id
        resp = self._client.get("/calculation/intervals", params=params)
        raise_for_response(resp)
        return StreamValues.model_validate(resp.json())

    def get_at_times(
        self,
        expression: str,
        times: Sequence[str],
        *,
        web_id: str | None = None,
    ) -> StreamValues:
        """Evaluate an expression at specific timestamps.

        Calls ``GET /calculation/times``.

        Args:
            expression: A PI performance equation expression.
            times: Sequence of PI time strings (e.g.
                ``["*-1h", "*-30m", "*"]``) at which to evaluate.
            web_id: Optional context WebID for relative tag references.

        Returns:
            A :class:`StreamValues` collection of calculated values.

        Raises:
            PIWebAPIError: If the expression is invalid or the server
                returns a non-2xx response.
        """
        params: list[tuple[str, str | int | float | bool | None]] = [
            ("expression", expression),
        ]
        for t in times:
            params.append(("time", t))
        if web_id is not None:
            params.append(("webId", web_id))
        resp = self._client.get("/calculation/times", params=params)
        raise_for_response(resp)
        return StreamValues.model_validate(resp.json())


class AsyncCalculationMixin:
    """Async methods for server-side expression evaluation.

    Mixed into the async client class.
    """

    _client: httpx.AsyncClient

    async def get_recorded(
        self,
        expression: str,
        start_time: str = "-1h",
        end_time: str = "*",
        *,
        web_id: str | None = None,
    ) -> StreamValues:
        """Evaluate an expression at the recorded event times of its inputs.

        Calls ``GET /calculation/recorded``.

        Args:
            expression: A PI performance equation expression, e.g.
                ``"'sinusoid' * 2 + 10"``.
            start_time: Start time as a PI time string. Defaults to
                ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"``
                (now).
            web_id: Optional WebID of a target PI Point or AF attribute
                to provide context for relative tag references.

        Returns:
            A :class:`StreamValues` collection of calculated values.

        Raises:
            PIWebAPIError: If the expression is invalid or the server
                returns a non-2xx response.
        """
        params: dict[str, str] = {
            "expression": expression,
            "startTime": start_time,
            "endTime": end_time,
        }
        if web_id is not None:
            validate_web_id(web_id, "web_id")
            params["webId"] = web_id
        resp = await self._client.get(
            "/calculation/recorded", params=params
        )
        await raise_for_response_async(resp)
        return StreamValues.model_validate(resp.json())

    async def get_summary(
        self,
        expression: str,
        start_time: str = "-1h",
        end_time: str = "*",
        summary_type: str = "All",
        calculation_basis: str = "TimeWeighted",
        *,
        web_id: str | None = None,
    ) -> StreamSummary:
        """Compute summary statistics of an expression over a time range.

        Calls ``GET /calculation/summary``.

        Args:
            expression: A PI performance equation expression.
            start_time: Start time as a PI time string. Defaults to
                ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"``
                (now).
            summary_type: Comma-separated list of summary types.
                Defaults to ``"All"``.
            calculation_basis: ``"TimeWeighted"`` (default) or
                ``"EventWeighted"``.
            web_id: Optional context WebID for relative tag references.

        Returns:
            A :class:`StreamSummary` with the requested statistics.

        Raises:
            PIWebAPIError: If the expression is invalid or the server
                returns a non-2xx response.
        """
        params: dict[str, str] = {
            "expression": expression,
            "startTime": start_time,
            "endTime": end_time,
            "summaryType": summary_type,
            "calculationBasis": calculation_basis,
        }
        if web_id is not None:
            validate_web_id(web_id, "web_id")
            params["webId"] = web_id
        resp = await self._client.get(
            "/calculation/summary", params=params
        )
        await raise_for_response_async(resp)
        return StreamSummary.model_validate(resp.json())

    async def get_at_intervals(
        self,
        expression: str,
        start_time: str = "-1h",
        end_time: str = "*",
        sample_interval: str = "10m",
        *,
        web_id: str | None = None,
    ) -> StreamValues:
        """Evaluate an expression at regular time intervals.

        Calls ``GET /calculation/intervals``.

        Args:
            expression: A PI performance equation expression.
            start_time: Start time as a PI time string. Defaults to
                ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"``
                (now).
            sample_interval: Evaluation interval (e.g. ``"10m"``,
                ``"1h"``). Defaults to ``"10m"``.
            web_id: Optional context WebID for relative tag references.

        Returns:
            A :class:`StreamValues` collection of calculated values.

        Raises:
            PIWebAPIError: If the expression is invalid or the server
                returns a non-2xx response.
        """
        params: dict[str, str] = {
            "expression": expression,
            "startTime": start_time,
            "endTime": end_time,
            "sampleInterval": sample_interval,
        }
        if web_id is not None:
            validate_web_id(web_id, "web_id")
            params["webId"] = web_id
        resp = await self._client.get(
            "/calculation/intervals", params=params
        )
        await raise_for_response_async(resp)
        return StreamValues.model_validate(resp.json())

    async def get_at_times(
        self,
        expression: str,
        times: Sequence[str],
        *,
        web_id: str | None = None,
    ) -> StreamValues:
        """Evaluate an expression at specific timestamps.

        Calls ``GET /calculation/times``.

        Args:
            expression: A PI performance equation expression.
            times: Sequence of PI time strings at which to evaluate.
            web_id: Optional context WebID for relative tag references.

        Returns:
            A :class:`StreamValues` collection of calculated values.

        Raises:
            PIWebAPIError: If the expression is invalid or the server
                returns a non-2xx response.
        """
        params: list[tuple[str, str | int | float | bool | None]] = [
            ("expression", expression),
        ]
        for t in times:
            params.append(("time", t))
        if web_id is not None:
            params.append(("webId", web_id))
        resp = await self._client.get(
            "/calculation/times", params=params
        )
        await raise_for_response_async(resp)
        return StreamValues.model_validate(resp.json())
