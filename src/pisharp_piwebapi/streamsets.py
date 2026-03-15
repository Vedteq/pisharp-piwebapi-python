"""Multi-stream (streamsets) read operations for PI Web API.

The ``/streamsets`` endpoints allow reading snapshot, recorded, or
interpolated values for **multiple WebIDs in a single HTTP request**,
which is far more efficient than issuing one ``/streams/{webId}/...`` call
per tag.  Use these methods when you need to poll or backfill many tags at
once.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from pisharp_piwebapi.exceptions import raise_for_response, raise_for_response_async
from pisharp_piwebapi.models import StreamSetItem, StreamValue

if TYPE_CHECKING:
    import httpx

# Alias for the params tuple type accepted by httpx.  Using the full union
# that httpx declares keeps mypy happy without casting everywhere.
_Param = tuple[str, str | int | float | bool | None]


def _parse_streamset_items(data: object) -> list[StreamSetItem]:
    """Coerce a raw API response into a list of :class:`StreamSetItem`.

    PI Web API wraps multi-stream responses in ``{"Items": [...]}`` when
    requesting recorded/interpolated values, but returns a plain list of
    objects (each with ``"WebId"``, ``"Value"``, etc.) for snapshot requests.
    This helper normalises both shapes.
    """
    if isinstance(data, dict):
        items = data.get("Items", data)
        if isinstance(items, list):
            return [StreamSetItem.model_validate(item) for item in items]
        return [StreamSetItem.model_validate(data)]
    if isinstance(data, list):
        return [StreamSetItem.model_validate(item) for item in data]
    return []


def _parse_snapshot_items(data: object) -> list[StreamValue]:
    """Coerce a snapshot streamset response into a flat list of :class:`StreamValue`.

    The ``/streamsets/value`` endpoint returns a list of objects each of
    which is shaped like a ``StreamValue`` (``Timestamp``, ``Value``, etc.)
    extended with identity fields (``WebId``, ``Name``, ``Path``).  We
    validate only the ``StreamValue`` fields here; callers who need the
    identity context should use :meth:`StreamSetsMixin.get_values_ad_hoc`
    instead.
    """
    if isinstance(data, dict):
        items: list[object] = data.get("Items", [])
    elif isinstance(data, list):
        items = data
    else:
        items = []
    return [StreamValue.model_validate(item) for item in items]


class StreamSetsMixin:
    """Methods for multi-stream reads via ``/streamsets``.

    Mixed into the sync client class.  All methods accept a list of WebIDs
    and translate them into repeated ``webId=`` query parameters, which is
    the format PI Web API expects for ad-hoc streamset requests.
    """

    _client: httpx.Client

    def get_values(self, web_ids: list[str]) -> list[StreamValue]:
        """Read the current (snapshot) value of multiple streams in one call.

        Calls ``GET /streamsets/value?webId=A&webId=B&...``.

        Args:
            web_ids: List of WebIDs to read.  The server preserves order.

        Returns:
            List of :class:`StreamValue` objects in the same order as
            ``web_ids``.  Each item carries the snapshot value and quality
            flags.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: list[_Param] = [("webId", wid) for wid in web_ids]
        resp = self._client.get("/streamsets/value", params=params)
        raise_for_response(resp)
        return _parse_snapshot_items(resp.json())

    def get_recorded_ad_hoc(
        self,
        web_ids: list[str],
        start_time: str = "-1h",
        end_time: str = "*",
        max_count: int = 1000,
    ) -> list[StreamSetItem]:
        """Read recorded (historian) values for multiple streams in one call.

        Calls ``GET /streamsets/recorded?webId=A&webId=B&...``.

        Args:
            web_ids: List of WebIDs to read.
            start_time: Start time as a PI time string (e.g. ``"-1h"``,
                ``"2024-01-01T00:00:00Z"``). Defaults to ``"-1h"``.
            end_time: End time as a PI time string. ``"*"`` means now.
                Defaults to ``"*"``.
            max_count: Maximum number of values **per stream** to return.
                Defaults to ``1000``.

        Returns:
            List of :class:`StreamSetItem` objects, one per WebID.  Each
            item's ``items`` list contains the recorded values for that
            stream.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: list[_Param] = [("webId", wid) for wid in web_ids]
        params += [
            ("startTime", start_time),
            ("endTime", end_time),
            ("maxCount", max_count),
        ]
        resp = self._client.get("/streamsets/recorded", params=params)
        raise_for_response(resp)
        return _parse_streamset_items(resp.json())

    def get_interpolated_ad_hoc(
        self,
        web_ids: list[str],
        start_time: str = "-1h",
        end_time: str = "*",
        interval: str = "10m",
    ) -> list[StreamSetItem]:
        """Read server-side interpolated values for multiple streams in one call.

        Calls ``GET /streamsets/interpolated?webId=A&webId=B&...``.

        Args:
            web_ids: List of WebIDs to read.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            interval: Interpolation interval (e.g. ``"10m"``, ``"1h"``).
                Defaults to ``"10m"``.

        Returns:
            List of :class:`StreamSetItem` objects, one per WebID.  Each
            item's ``items`` list contains the interpolated values for that
            stream.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: list[_Param] = [("webId", wid) for wid in web_ids]
        params += [
            ("startTime", start_time),
            ("endTime", end_time),
            ("interval", interval),
        ]
        resp = self._client.get("/streamsets/interpolated", params=params)
        raise_for_response(resp)
        return _parse_streamset_items(resp.json())

    def get_recorded_by_element(
        self,
        element_web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        max_count: int = 1000,
        name_filter: str = "*",
    ) -> list[StreamSetItem]:
        """Read recorded values for all attributes of an AF element.

        Calls ``GET /streamsets/{elementWebId}/recorded``.  This is the
        element-scoped variant that does not require enumerating individual
        attribute WebIDs.

        Args:
            element_web_id: WebID of the AF element.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            max_count: Maximum number of values per attribute. Defaults to
                ``1000``.
            name_filter: Attribute name pattern. Defaults to ``"*"`` (all).

        Returns:
            List of :class:`StreamSetItem` objects, one per attribute.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            f"/streamsets/{quote(element_web_id, safe='')}/recorded",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "maxCount": max_count,
                "nameFilter": name_filter,
            },
        )
        raise_for_response(resp)
        return _parse_streamset_items(resp.json())

    def get_interpolated_by_element(
        self,
        element_web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        interval: str = "10m",
        name_filter: str = "*",
    ) -> list[StreamSetItem]:
        """Read server-side interpolated values for all attributes of an AF element.

        Calls ``GET /streamsets/{elementWebId}/interpolated``.  PI Web API
        computes values at regular ``interval`` steps between ``start_time``
        and ``end_time`` for every attribute on the element that matches
        ``name_filter``.

        Args:
            element_web_id: WebID of the AF element.
            start_time: Start time as a PI time string (e.g. ``"-4h"``,
                ``"2024-01-01T00:00:00Z"``). Defaults to ``"-1h"``.
            end_time: End time as a PI time string. ``"*"`` means now.
                Defaults to ``"*"``.
            interval: Interpolation interval (e.g. ``"10m"``, ``"1h"``).
                Defaults to ``"10m"``.
            name_filter: Attribute name pattern supporting wildcards.
                Defaults to ``"*"`` (all attributes).

        Returns:
            List of :class:`StreamSetItem` objects, one per attribute.  Each
            item's ``items`` list contains the interpolated values for that
            attribute over the requested time range.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            f"/streamsets/{quote(element_web_id, safe='')}/interpolated",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "interval": interval,
                "nameFilter": name_filter,
            },
        )
        raise_for_response(resp)
        return _parse_streamset_items(resp.json())


class AsyncStreamSetsMixin:
    """Async methods for multi-stream reads via ``/streamsets``.

    Mixed into the async client class.
    """

    _client: httpx.AsyncClient

    async def get_values(self, web_ids: list[str]) -> list[StreamValue]:
        """Read the current (snapshot) value of multiple streams in one call.

        Calls ``GET /streamsets/value?webId=A&webId=B&...``.

        Args:
            web_ids: List of WebIDs to read.

        Returns:
            List of :class:`StreamValue` objects in the same order as
            ``web_ids``.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: list[_Param] = [("webId", wid) for wid in web_ids]
        resp = await self._client.get("/streamsets/value", params=params)
        await raise_for_response_async(resp)
        return _parse_snapshot_items(resp.json())

    async def get_recorded_ad_hoc(
        self,
        web_ids: list[str],
        start_time: str = "-1h",
        end_time: str = "*",
        max_count: int = 1000,
    ) -> list[StreamSetItem]:
        """Read recorded (historian) values for multiple streams in one call.

        Calls ``GET /streamsets/recorded?webId=A&webId=B&...``.

        Args:
            web_ids: List of WebIDs to read.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            max_count: Maximum number of values per stream. Defaults to ``1000``.

        Returns:
            List of :class:`StreamSetItem` objects, one per WebID.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: list[_Param] = [("webId", wid) for wid in web_ids]
        params += [
            ("startTime", start_time),
            ("endTime", end_time),
            ("maxCount", max_count),
        ]
        resp = await self._client.get("/streamsets/recorded", params=params)
        await raise_for_response_async(resp)
        return _parse_streamset_items(resp.json())

    async def get_interpolated_ad_hoc(
        self,
        web_ids: list[str],
        start_time: str = "-1h",
        end_time: str = "*",
        interval: str = "10m",
    ) -> list[StreamSetItem]:
        """Read server-side interpolated values for multiple streams in one call.

        Calls ``GET /streamsets/interpolated?webId=A&webId=B&...``.

        Args:
            web_ids: List of WebIDs to read.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            interval: Interpolation interval (e.g. ``"10m"``, ``"1h"``).
                Defaults to ``"10m"``.

        Returns:
            List of :class:`StreamSetItem` objects, one per WebID.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: list[_Param] = [("webId", wid) for wid in web_ids]
        params += [
            ("startTime", start_time),
            ("endTime", end_time),
            ("interval", interval),
        ]
        resp = await self._client.get("/streamsets/interpolated", params=params)
        await raise_for_response_async(resp)
        return _parse_streamset_items(resp.json())

    async def get_recorded_by_element(
        self,
        element_web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        max_count: int = 1000,
        name_filter: str = "*",
    ) -> list[StreamSetItem]:
        """Read recorded values for all attributes of an AF element.

        Calls ``GET /streamsets/{elementWebId}/recorded``.

        Args:
            element_web_id: WebID of the AF element.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            max_count: Maximum number of values per attribute. Defaults to
                ``1000``.
            name_filter: Attribute name pattern. Defaults to ``"*"`` (all).

        Returns:
            List of :class:`StreamSetItem` objects, one per attribute.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/streamsets/{quote(element_web_id, safe='')}/recorded",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "maxCount": max_count,
                "nameFilter": name_filter,
            },
        )
        await raise_for_response_async(resp)
        return _parse_streamset_items(resp.json())

    async def get_interpolated_by_element(
        self,
        element_web_id: str,
        start_time: str = "-1h",
        end_time: str = "*",
        interval: str = "10m",
        name_filter: str = "*",
    ) -> list[StreamSetItem]:
        """Read server-side interpolated values for all attributes of an AF element.

        Calls ``GET /streamsets/{elementWebId}/interpolated``.

        Args:
            element_web_id: WebID of the AF element.
            start_time: Start time as a PI time string. Defaults to ``"-1h"``.
            end_time: End time as a PI time string. Defaults to ``"*"`` (now).
            interval: Interpolation interval (e.g. ``"10m"``, ``"1h"``).
                Defaults to ``"10m"``.
            name_filter: Attribute name pattern supporting wildcards.
                Defaults to ``"*"`` (all attributes).

        Returns:
            List of :class:`StreamSetItem` objects, one per attribute.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/streamsets/{quote(element_web_id, safe='')}/interpolated",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "interval": interval,
                "nameFilter": name_filter,
            },
        )
        await raise_for_response_async(resp)
        return _parse_streamset_items(resp.json())
