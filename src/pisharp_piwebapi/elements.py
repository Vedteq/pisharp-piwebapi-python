"""AF (Asset Framework) element and database operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from pisharp_piwebapi.exceptions import raise_for_response, raise_for_response_async
from pisharp_piwebapi.models import PIAttribute, PIDatabase, PIElement

if TYPE_CHECKING:
    import httpx


class ElementsMixin:
    """Methods for AF element and database lookup. Mixed into the sync client class."""

    _client: httpx.Client

    def get_databases(self, asset_server_web_id: str) -> list[PIDatabase]:
        """Return all AF databases on an Asset Server.

        Args:
            asset_server_web_id: WebID of the PI Asset Server (AF Server).

        Returns:
            List of :class:`PIDatabase` objects.

        Raises:
            NotFoundError: If the Asset Server WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            f"/assetservers/{quote(asset_server_web_id, safe='')}/assetdatabases"
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIDatabase.model_validate(item) for item in items]

    def get_database(self, web_id: str) -> PIDatabase:
        """Return a single AF database by its WebID.

        Args:
            web_id: WebID of the PI AF Database.

        Returns:
            A :class:`PIDatabase` populated from the API response.

        Raises:
            NotFoundError: If no database with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(f"/assetdatabases/{quote(web_id, safe='')}")
        raise_for_response(resp)
        return PIDatabase.model_validate(resp.json())

    def get_database_by_path(self, path: str) -> PIDatabase:
        """Look up an AF database by its full path.

        Args:
            path: Full AF database path, e.g. ``"\\\\AF_SERVER\\DATABASE"``.

        Returns:
            A :class:`PIDatabase` populated from the API response.

        Raises:
            NotFoundError: If the database path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/assetdatabases", params={"path": path})
        raise_for_response(resp)
        return PIDatabase.model_validate(resp.json())

    def get_elements(
        self,
        database_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIElement]:
        """Return top-level AF elements in a database.

        Args:
            database_web_id: WebID of the AF database.
            name_filter: Name pattern supporting wildcards, e.g. ``"Reactor*"``.
                Defaults to ``"*"`` (all elements).
            max_count: Maximum number of results to return. Defaults to ``100``.

        Returns:
            List of :class:`PIElement` objects.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            f"/assetdatabases/{quote(database_web_id, safe='')}/elements",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIElement.model_validate(item) for item in items]

    def get_element(self, web_id: str) -> PIElement:
        """Return a single AF element by its WebID.

        Args:
            web_id: WebID of the AF element.

        Returns:
            A :class:`PIElement` populated from the API response.

        Raises:
            NotFoundError: If no element with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(f"/elements/{quote(web_id, safe='')}")
        raise_for_response(resp)
        return PIElement.model_validate(resp.json())

    def get_element_by_path(self, path: str) -> PIElement:
        """Look up an AF element by its full path.

        Args:
            path: Full AF element path, e.g.
                ``"\\\\AF_SERVER\\DATABASE\\ELEMENT"``.

        Returns:
            A :class:`PIElement` populated from the API response.

        Raises:
            NotFoundError: If the element path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/elements", params={"path": path})
        raise_for_response(resp)
        return PIElement.model_validate(resp.json())

    def get_child_elements(
        self,
        parent_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIElement]:
        """Return direct child elements of an AF element.

        Args:
            parent_web_id: WebID of the parent AF element.
            name_filter: Name pattern supporting wildcards. Defaults to ``"*"``.
            max_count: Maximum number of results to return. Defaults to ``100``.

        Returns:
            List of child :class:`PIElement` objects.

        Raises:
            NotFoundError: If the parent element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            f"/elements/{quote(parent_web_id, safe='')}/elements",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIElement.model_validate(item) for item in items]

    def get_attributes(
        self,
        element_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIAttribute]:
        """Return AF attributes of an element.

        Args:
            element_web_id: WebID of the AF element.
            name_filter: Name pattern supporting wildcards. Defaults to ``"*"``.
            max_count: Maximum number of results to return. Defaults to ``100``.

        Returns:
            List of :class:`PIAttribute` objects.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            f"/elements/{quote(element_web_id, safe='')}/attributes",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIAttribute.model_validate(item) for item in items]

    def get_attribute(self, web_id: str) -> PIAttribute:
        """Return a single AF attribute by its WebID.

        Args:
            web_id: WebID of the AF attribute.

        Returns:
            A :class:`PIAttribute` populated from the API response.

        Raises:
            NotFoundError: If no attribute with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(f"/attributes/{quote(web_id, safe='')}")
        raise_for_response(resp)
        return PIAttribute.model_validate(resp.json())


class AsyncElementsMixin:
    """Async methods for AF element and database lookup. Mixed into the async client class."""

    _client: httpx.AsyncClient

    async def get_databases(self, asset_server_web_id: str) -> list[PIDatabase]:
        """Return all AF databases on an Asset Server.

        Args:
            asset_server_web_id: WebID of the PI Asset Server (AF Server).

        Returns:
            List of :class:`PIDatabase` objects.

        Raises:
            NotFoundError: If the Asset Server WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/assetservers/{quote(asset_server_web_id, safe='')}/assetdatabases"
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIDatabase.model_validate(item) for item in items]

    async def get_database(self, web_id: str) -> PIDatabase:
        """Return a single AF database by its WebID.

        Args:
            web_id: WebID of the PI AF Database.

        Returns:
            A :class:`PIDatabase` populated from the API response.

        Raises:
            NotFoundError: If no database with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(f"/assetdatabases/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
        return PIDatabase.model_validate(resp.json())

    async def get_database_by_path(self, path: str) -> PIDatabase:
        """Look up an AF database by its full path.

        Args:
            path: Full AF database path, e.g. ``"\\\\AF_SERVER\\DATABASE"``.

        Returns:
            A :class:`PIDatabase` populated from the API response.

        Raises:
            NotFoundError: If the database path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get("/assetdatabases", params={"path": path})
        await raise_for_response_async(resp)
        return PIDatabase.model_validate(resp.json())

    async def get_elements(
        self,
        database_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIElement]:
        """Return top-level AF elements in a database.

        Args:
            database_web_id: WebID of the AF database.
            name_filter: Name pattern supporting wildcards. Defaults to ``"*"``.
            max_count: Maximum number of results to return. Defaults to ``100``.

        Returns:
            List of :class:`PIElement` objects.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/assetdatabases/{quote(database_web_id, safe='')}/elements",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIElement.model_validate(item) for item in items]

    async def get_element(self, web_id: str) -> PIElement:
        """Return a single AF element by its WebID.

        Args:
            web_id: WebID of the AF element.

        Returns:
            A :class:`PIElement` populated from the API response.

        Raises:
            NotFoundError: If no element with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(f"/elements/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
        return PIElement.model_validate(resp.json())

    async def get_element_by_path(self, path: str) -> PIElement:
        """Look up an AF element by its full path.

        Args:
            path: Full AF element path, e.g.
                ``"\\\\AF_SERVER\\DATABASE\\ELEMENT"``.

        Returns:
            A :class:`PIElement` populated from the API response.

        Raises:
            NotFoundError: If the element path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get("/elements", params={"path": path})
        await raise_for_response_async(resp)
        return PIElement.model_validate(resp.json())

    async def get_child_elements(
        self,
        parent_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIElement]:
        """Return direct child elements of an AF element.

        Args:
            parent_web_id: WebID of the parent AF element.
            name_filter: Name pattern supporting wildcards. Defaults to ``"*"``.
            max_count: Maximum number of results to return. Defaults to ``100``.

        Returns:
            List of child :class:`PIElement` objects.

        Raises:
            NotFoundError: If the parent element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/elements/{quote(parent_web_id, safe='')}/elements",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIElement.model_validate(item) for item in items]

    async def get_attributes(
        self,
        element_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIAttribute]:
        """Return AF attributes of an element.

        Args:
            element_web_id: WebID of the AF element.
            name_filter: Name pattern supporting wildcards. Defaults to ``"*"``.
            max_count: Maximum number of results to return. Defaults to ``100``.

        Returns:
            List of :class:`PIAttribute` objects.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/elements/{quote(element_web_id, safe='')}/attributes",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIAttribute.model_validate(item) for item in items]

    async def get_attribute(self, web_id: str) -> PIAttribute:
        """Return a single AF attribute by its WebID.

        Args:
            web_id: WebID of the AF attribute.

        Returns:
            A :class:`PIAttribute` populated from the API response.

        Raises:
            NotFoundError: If no attribute with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(f"/attributes/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
        return PIAttribute.model_validate(resp.json())
