"""Element and attribute operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.models import PIAttribute, PIElement

if TYPE_CHECKING:
    import httpx


class ElementsMixin:
    """Methods for PI AF Element operations. Mixed into client classes."""

    _client: httpx.Client

    def get_by_path(self, path: str) -> PIElement:
        """Look up an AF Element by its full path.

        Args:
            path: Full element path, e.g. r"\\\\AF\\DB\\Element"
        """
        resp = self._client.get("/elements", params={"path": path})
        resp.raise_for_status()
        return PIElement.model_validate(resp.json())

    def get_by_web_id(self, web_id: str) -> PIElement:
        """Look up an AF Element by its WebID."""
        resp = self._client.get(f"/elements/{quote(web_id, safe='')}")
        resp.raise_for_status()
        return PIElement.model_validate(resp.json())

    def get_children(
        self,
        web_id: str,
        max_count: int = 1000,
    ) -> list[PIElement]:
        """Get child elements of an AF Element."""
        resp = self._client.get(
            f"/elements/{quote(web_id, safe='')}/elements",
            params={"maxCount": max_count},
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIElement.model_validate(item) for item in items]

    def get_attributes(
        self,
        web_id: str,
        max_count: int = 1000,
    ) -> list[PIAttribute]:
        """Get attributes of an AF Element."""
        resp = self._client.get(
            f"/elements/{quote(web_id, safe='')}/attributes",
            params={"maxCount": max_count},
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIAttribute.model_validate(item) for item in items]

    def create(
        self,
        parent_web_id: str,
        name: str,
        description: str = "",
        template_name: str = "",
    ) -> None:
        """Create a child element under a parent element."""
        body: dict[str, Any] = {"Name": name}
        if description:
            body["Description"] = description
        if template_name:
            body["TemplateName"] = template_name
        resp = self._client.post(
            f"/elements/{quote(parent_web_id, safe='')}/elements",
            json=body,
        )
        resp.raise_for_status()

    def delete(self, web_id: str) -> None:
        """Delete an AF Element."""
        resp = self._client.delete(f"/elements/{quote(web_id, safe='')}")
        resp.raise_for_status()


class AsyncElementsMixin:
    """Async methods for PI AF Element operations."""

    _client: httpx.AsyncClient  # type: ignore[assignment]

    async def get_by_path(self, path: str) -> PIElement:
        """Look up an AF Element by its full path (async)."""
        resp = await self._client.get("/elements", params={"path": path})
        resp.raise_for_status()
        return PIElement.model_validate(resp.json())

    async def get_by_web_id(self, web_id: str) -> PIElement:
        """Look up an AF Element by its WebID (async)."""
        resp = await self._client.get(f"/elements/{quote(web_id, safe='')}")
        resp.raise_for_status()
        return PIElement.model_validate(resp.json())

    async def get_children(
        self,
        web_id: str,
        max_count: int = 1000,
    ) -> list[PIElement]:
        """Get child elements of an AF Element (async)."""
        resp = await self._client.get(
            f"/elements/{quote(web_id, safe='')}/elements",
            params={"maxCount": max_count},
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIElement.model_validate(item) for item in items]

    async def get_attributes(
        self,
        web_id: str,
        max_count: int = 1000,
    ) -> list[PIAttribute]:
        """Get attributes of an AF Element (async)."""
        resp = await self._client.get(
            f"/elements/{quote(web_id, safe='')}/attributes",
            params={"maxCount": max_count},
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIAttribute.model_validate(item) for item in items]

    async def create(
        self,
        parent_web_id: str,
        name: str,
        description: str = "",
        template_name: str = "",
    ) -> None:
        """Create a child element under a parent element (async)."""
        body: dict[str, Any] = {"Name": name}
        if description:
            body["Description"] = description
        if template_name:
            body["TemplateName"] = template_name
        resp = await self._client.post(
            f"/elements/{quote(parent_web_id, safe='')}/elements",
            json=body,
        )
        resp.raise_for_status()

    async def delete(self, web_id: str) -> None:
        """Delete an AF Element (async)."""
        resp = await self._client.delete(f"/elements/{quote(web_id, safe='')}")
        resp.raise_for_status()
