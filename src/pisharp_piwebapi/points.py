"""Point and attribute lookup operations."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from pisharp_piwebapi.models import PIPoint

if TYPE_CHECKING:
    import httpx


class PointsMixin:
    """Methods for PI Point lookup. Mixed into the client classes."""

    _client: httpx.Client

    def get_by_path(self, path: str) -> PIPoint:
        """Look up a PI Point by its full path.

        Args:
            path: Full PI point path, e.g. r"\\\\SERVER\\sinusoid"

        Returns:
            PIPoint with the point's metadata and WebId.
        """
        resp = self._client.get("/points", params={"path": path})
        resp.raise_for_status()
        return PIPoint.model_validate(resp.json())

    def get_by_web_id(self, web_id: str) -> PIPoint:
        """Look up a PI Point by its WebID.

        Args:
            web_id: The WebID of the point.

        Returns:
            PIPoint with the point's metadata.
        """
        resp = self._client.get(f"/points/{quote(web_id, safe='')}")
        resp.raise_for_status()
        return PIPoint.model_validate(resp.json())

    def search(self, query: str, max_count: int = 100) -> list[PIPoint]:
        """Search for PI Points by name pattern.

        Args:
            query: Name query (supports wildcards, e.g. "sinu*").
            max_count: Maximum number of results.

        Returns:
            List of matching PIPoint objects.
        """
        resp = self._client.get(
            "/points/search",
            params={"q": query, "maxCount": max_count},
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIPoint.model_validate(item) for item in items]


class AsyncPointsMixin:
    """Async methods for PI Point lookup."""

    _client: httpx.AsyncClient  # type: ignore[assignment]

    async def get_by_path(self, path: str) -> PIPoint:
        """Look up a PI Point by its full path (async)."""
        resp = await self._client.get("/points", params={"path": path})
        resp.raise_for_status()
        return PIPoint.model_validate(resp.json())

    async def get_by_web_id(self, web_id: str) -> PIPoint:
        """Look up a PI Point by its WebID (async)."""
        resp = await self._client.get(f"/points/{quote(web_id, safe='')}")
        resp.raise_for_status()
        return PIPoint.model_validate(resp.json())

    async def search(self, query: str, max_count: int = 100) -> list[PIPoint]:
        """Search for PI Points by name pattern (async)."""
        resp = await self._client.get(
            "/points/search",
            params={"q": query, "maxCount": max_count},
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIPoint.model_validate(item) for item in items]
