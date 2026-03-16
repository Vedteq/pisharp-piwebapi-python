"""Event Frame operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.models import EventFrame

if TYPE_CHECKING:
    import httpx


class EventFramesMixin:
    """Methods for PI AF Event Frame operations. Mixed into client classes."""

    _client: httpx.Client

    def get_by_web_id(self, web_id: str) -> EventFrame:
        """Look up an Event Frame by its WebID."""
        resp = self._client.get(f"/eventframes/{quote(web_id, safe='')}")
        resp.raise_for_status()
        return EventFrame.model_validate(resp.json())

    def search(
        self,
        query: str,
        *,
        database_web_id: str | None = None,
        start_time: str = "*-1d",
        end_time: str = "*",
        max_count: int = 100,
    ) -> list[EventFrame]:
        """Search for Event Frames.

        Args:
            query: Search query string.
            database_web_id: Limit search to a specific AF database.
            start_time: Start of the time range.
            end_time: End of the time range.
            max_count: Maximum results to return.
        """
        params: dict[str, Any] = {
            "q": query,
            "startTime": start_time,
            "endTime": end_time,
            "maxCount": max_count,
        }
        if database_web_id:
            params["databaseWebId"] = database_web_id
        resp = self._client.get("/eventframes/search", params=params)
        resp.raise_for_status()
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
        """Get Event Frames associated with an element."""
        resp = self._client.get(
            f"/elements/{quote(element_web_id, safe='')}/eventframes",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "maxCount": max_count,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [EventFrame.model_validate(item) for item in items]

    def acknowledge(self, web_id: str) -> None:
        """Acknowledge an Event Frame."""
        resp = self._client.patch(
            f"/eventframes/{quote(web_id, safe='')}",
            json={"IsAcknowledged": True},
        )
        resp.raise_for_status()

    def create(
        self,
        element_web_id: str,
        name: str,
        start_time: str,
        end_time: str,
        *,
        description: str = "",
        template_name: str = "",
        severity: str = "None",
    ) -> None:
        """Create an Event Frame on an element."""
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
        resp = self._client.post(
            f"/elements/{quote(element_web_id, safe='')}/eventframes",
            json=body,
        )
        resp.raise_for_status()

    def delete(self, web_id: str) -> None:
        """Delete an Event Frame."""
        resp = self._client.delete(f"/eventframes/{quote(web_id, safe='')}")
        resp.raise_for_status()


class AsyncEventFramesMixin:
    """Async methods for PI AF Event Frame operations."""

    _client: httpx.AsyncClient  # type: ignore[assignment]

    async def get_by_web_id(self, web_id: str) -> EventFrame:
        """Look up an Event Frame by its WebID (async)."""
        resp = await self._client.get(f"/eventframes/{quote(web_id, safe='')}")
        resp.raise_for_status()
        return EventFrame.model_validate(resp.json())

    async def search(
        self,
        query: str,
        *,
        database_web_id: str | None = None,
        start_time: str = "*-1d",
        end_time: str = "*",
        max_count: int = 100,
    ) -> list[EventFrame]:
        """Search for Event Frames (async)."""
        params: dict[str, Any] = {
            "q": query,
            "startTime": start_time,
            "endTime": end_time,
            "maxCount": max_count,
        }
        if database_web_id:
            params["databaseWebId"] = database_web_id
        resp = await self._client.get("/eventframes/search", params=params)
        resp.raise_for_status()
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
        """Get Event Frames associated with an element (async)."""
        resp = await self._client.get(
            f"/elements/{quote(element_web_id, safe='')}/eventframes",
            params={
                "startTime": start_time,
                "endTime": end_time,
                "maxCount": max_count,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [EventFrame.model_validate(item) for item in items]

    async def acknowledge(self, web_id: str) -> None:
        """Acknowledge an Event Frame (async)."""
        resp = await self._client.patch(
            f"/eventframes/{quote(web_id, safe='')}",
            json={"IsAcknowledged": True},
        )
        resp.raise_for_status()

    async def create(
        self,
        element_web_id: str,
        name: str,
        start_time: str,
        end_time: str,
        *,
        description: str = "",
        template_name: str = "",
        severity: str = "None",
    ) -> None:
        """Create an Event Frame on an element (async)."""
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
        resp = await self._client.post(
            f"/elements/{quote(element_web_id, safe='')}/eventframes",
            json=body,
        )
        resp.raise_for_status()

    async def delete(self, web_id: str) -> None:
        """Delete an Event Frame (async)."""
        resp = await self._client.delete(f"/eventframes/{quote(web_id, safe='')}")
        resp.raise_for_status()
