"""Event Frame operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import EventFrame

if TYPE_CHECKING:
    import httpx


class EventFramesMixin:
    """Methods for PI AF Event Frame operations. Mixed into client classes."""

    _client: httpx.Client

    def get_by_web_id(self, web_id: str) -> EventFrame:
        """Look up an Event Frame by its WebID.

        Args:
            web_id: WebID of the Event Frame.

        Returns:
            An :class:`EventFrame` populated from the API response.

        Raises:
            NotFoundError: If no Event Frame with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(f"/eventframes/{quote(web_id, safe='')}")
        raise_for_response(resp)
        return EventFrame.model_validate(resp.json())

    def search(
        self,
        database_web_id: str,
        *,
        name_filter: str = "*",
        start_time: str = "*-1d",
        end_time: str = "*",
        max_count: int = 100,
    ) -> list[EventFrame]:
        """Search for Event Frames within an AF database.

        Calls ``GET /assetdatabases/{webId}/eventframes``.

        Args:
            database_web_id: WebID of the AF database to search.
            name_filter: Name pattern supporting wildcards (e.g.
                ``"Alarm*"``). Defaults to ``"*"`` (all event frames).
            start_time: Start of the time range. Defaults to ``"*-1d"``.
            end_time: End of the time range. Defaults to ``"*"``.
            max_count: Maximum results to return. Defaults to ``100``.

        Returns:
            List of :class:`EventFrame` objects matching the search criteria.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(database_web_id, "database_web_id")
        params: dict[str, Any] = {
            "nameFilter": name_filter,
            "startTime": start_time,
            "endTime": end_time,
            "maxCount": max_count,
        }
        resp = self._client.get(
            f"/assetdatabases/{quote(database_web_id, safe='')}/eventframes",
            params=params,
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [EventFrame.model_validate(item) for item in items]

    def get_by_element(
        self,
        element_web_id: str,
        *,
        start_time: str = "*-1d",
        end_time: str = "*",
        max_count: int = 100,
    ) -> list[EventFrame]:
        """Get Event Frames associated with an element.

        Args:
            element_web_id: WebID of the AF element.
            start_time: Start of the time range.
            end_time: End of the time range.
            max_count: Maximum results to return.

        Returns:
            List of :class:`EventFrame` objects.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(element_web_id, "element_web_id")
        resp = self._client.get(
            f"/elements/{quote(element_web_id, safe='')}/eventframes",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "maxCount": max_count,
            },
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [EventFrame.model_validate(item) for item in items]

    def acknowledge(self, web_id: str) -> None:
        """Acknowledge an Event Frame.

        Args:
            web_id: WebID of the Event Frame to acknowledge.

        Raises:
            NotFoundError: If no Event Frame with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"/eventframes/{quote(web_id, safe='')}",
            json={"IsAcknowledged": True},
        )
        raise_for_response(resp)

    def create(
        self,
        database_web_id: str,
        name: str,
        start_time: str,
        end_time: str,
        *,
        description: str = "",
        template_name: str = "",
        severity: str = "None",
        ref_element_web_ids: list[str] | None = None,
    ) -> None:
        """Create an Event Frame in an AF database.

        Calls ``POST /assetdatabases/{webId}/eventframes``.

        Args:
            database_web_id: WebID of the AF database to create the
                event frame in.
            name: Name for the new Event Frame.
            start_time: Start time as a PI time string.
            end_time: End time as a PI time string.
            description: Optional description.
            template_name: Optional AF event frame template name.
            severity: Severity level. Defaults to ``"None"``.
            ref_element_web_ids: Optional list of AF element WebIDs to
                associate with the event frame.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(database_web_id, "database_web_id")
        body: dict[str, Any] = {
            "Name": name,
            "StartTime": start_time,
            "EndTime": end_time,
        }
        if description:
            body["Description"] = description
        if template_name:
            body["TemplateName"] = template_name
        if severity != "None":
            body["Severity"] = severity
        if ref_element_web_ids:
            body["RefElementWebIds"] = ref_element_web_ids
        resp = self._client.post(
            f"/assetdatabases/{quote(database_web_id, safe='')}/eventframes",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete an Event Frame.

        Args:
            web_id: WebID of the Event Frame to delete.

        Raises:
            NotFoundError: If no Event Frame with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(f"/eventframes/{quote(web_id, safe='')}")
        raise_for_response(resp)


class AsyncEventFramesMixin:
    """Async methods for PI AF Event Frame operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(self, web_id: str) -> EventFrame:
        """Look up an Event Frame by its WebID.

        Args:
            web_id: WebID of the Event Frame.

        Returns:
            An :class:`EventFrame` populated from the API response.

        Raises:
            NotFoundError: If no Event Frame with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(f"/eventframes/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
        return EventFrame.model_validate(resp.json())

    async def search(
        self,
        database_web_id: str,
        *,
        name_filter: str = "*",
        start_time: str = "*-1d",
        end_time: str = "*",
        max_count: int = 100,
    ) -> list[EventFrame]:
        """Search for Event Frames within an AF database.

        Calls ``GET /assetdatabases/{webId}/eventframes``.

        Args:
            database_web_id: WebID of the AF database to search.
            name_filter: Name pattern supporting wildcards (e.g.
                ``"Alarm*"``). Defaults to ``"*"`` (all event frames).
            start_time: Start of the time range. Defaults to ``"*-1d"``.
            end_time: End of the time range. Defaults to ``"*"``.
            max_count: Maximum results to return. Defaults to ``100``.

        Returns:
            List of :class:`EventFrame` objects matching the search criteria.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(database_web_id, "database_web_id")
        params: dict[str, Any] = {
            "nameFilter": name_filter,
            "startTime": start_time,
            "endTime": end_time,
            "maxCount": max_count,
        }
        resp = await self._client.get(
            f"/assetdatabases/{quote(database_web_id, safe='')}/eventframes",
            params=params,
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [EventFrame.model_validate(item) for item in items]

    async def get_by_element(
        self,
        element_web_id: str,
        *,
        start_time: str = "*-1d",
        end_time: str = "*",
        max_count: int = 100,
    ) -> list[EventFrame]:
        """Get Event Frames associated with an element.

        Args:
            element_web_id: WebID of the AF element.
            start_time: Start of the time range.
            end_time: End of the time range.
            max_count: Maximum results to return.

        Returns:
            List of :class:`EventFrame` objects.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(element_web_id, "element_web_id")
        resp = await self._client.get(
            f"/elements/{quote(element_web_id, safe='')}/eventframes",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "maxCount": max_count,
            },
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [EventFrame.model_validate(item) for item in items]

    async def acknowledge(self, web_id: str) -> None:
        """Acknowledge an Event Frame.

        Args:
            web_id: WebID of the Event Frame to acknowledge.

        Raises:
            NotFoundError: If no Event Frame with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"/eventframes/{quote(web_id, safe='')}",
            json={"IsAcknowledged": True},
        )
        await raise_for_response_async(resp)

    async def create(
        self,
        database_web_id: str,
        name: str,
        start_time: str,
        end_time: str,
        *,
        description: str = "",
        template_name: str = "",
        severity: str = "None",
        ref_element_web_ids: list[str] | None = None,
    ) -> None:
        """Create an Event Frame in an AF database.

        Calls ``POST /assetdatabases/{webId}/eventframes``.

        Args:
            database_web_id: WebID of the AF database to create the
                event frame in.
            name: Name for the new Event Frame.
            start_time: Start time as a PI time string.
            end_time: End time as a PI time string.
            description: Optional description.
            template_name: Optional AF event frame template name.
            severity: Severity level. Defaults to ``"None"``.
            ref_element_web_ids: Optional list of AF element WebIDs to
                associate with the event frame.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(database_web_id, "database_web_id")
        body: dict[str, Any] = {
            "Name": name,
            "StartTime": start_time,
            "EndTime": end_time,
        }
        if description:
            body["Description"] = description
        if template_name:
            body["TemplateName"] = template_name
        if severity != "None":
            body["Severity"] = severity
        if ref_element_web_ids:
            body["RefElementWebIds"] = ref_element_web_ids
        resp = await self._client.post(
            f"/assetdatabases/{quote(database_web_id, safe='')}/eventframes",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete an Event Frame.

        Args:
            web_id: WebID of the Event Frame to delete.

        Raises:
            NotFoundError: If no Event Frame with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(f"/eventframes/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
