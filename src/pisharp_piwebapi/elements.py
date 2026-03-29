"""AF (Asset Framework) element and database operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import raise_for_response, raise_for_response_async
from pisharp_piwebapi.models import (
    PIAssetServer,
    PIAttribute,
    PIDatabase,
    PIElement,
    StreamValue,
)

if TYPE_CHECKING:
    import httpx


class ElementsMixin:
    """Methods for AF element and database lookup. Mixed into the sync client class."""

    _client: httpx.Client

    def get_asset_servers(self) -> list[PIAssetServer]:
        """Return all PI Asset Servers (AF Servers) registered with PI Web API.

        This is the natural starting point for AF hierarchy traversal.  Call
        :meth:`get_databases` with the :attr:`~PIAssetServer.web_id` of a
        returned server to list the AF databases hosted on it.

        Returns:
            List of :class:`PIAssetServer` objects.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/assetservers")
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIAssetServer.model_validate(item) for item in items]

    def get_asset_server(self, web_id: str) -> PIAssetServer:
        """Return a single PI Asset Server by its WebID.

        Args:
            web_id: WebID of the PI Asset Server.

        Returns:
            A :class:`PIAssetServer` populated from the API response.

        Raises:
            NotFoundError: If no asset server with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(f"/assetservers/{quote(web_id, safe='')}")
        raise_for_response(resp)
        return PIAssetServer.model_validate(resp.json())

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
        search_full_hierarchy: bool = False,
    ) -> list[PIElement]:
        """Return AF elements in a database.

        By default only top-level (root) elements are returned.  Set
        ``search_full_hierarchy=True`` to traverse the entire element tree and
        return all matching elements at any depth.

        Args:
            database_web_id: WebID of the AF database.
            name_filter: Name pattern supporting wildcards, e.g. ``"Reactor*"``.
                Defaults to ``"*"`` (all elements).
            max_count: Maximum number of results to return. Defaults to ``100``.
            search_full_hierarchy: When ``True``, the PI Web API server searches
                recursively through all child elements.  Defaults to ``False``
                (top-level only).

        Returns:
            List of :class:`PIElement` objects.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: dict[str, str | int | bool] = {
            "nameFilter": name_filter,
            "maxCount": max_count,
        }
        if search_full_hierarchy:
            params["searchFullHierarchy"] = True
        resp = self._client.get(
            f"/assetdatabases/{quote(database_web_id, safe='')}/elements",
            params=params,
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

    def get_attribute_by_path(self, path: str) -> PIAttribute:
        """Look up an AF attribute by its full path.

        The path uses a pipe (``|``) to separate the element path from the
        attribute name, e.g. ``"\\\\AF_SERVER\\DB\\Element|Temperature"``.

        Args:
            path: Full AF attribute path.

        Returns:
            A :class:`PIAttribute` populated from the API response.

        Raises:
            NotFoundError: If the attribute path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/attributes", params={"path": path})
        raise_for_response(resp)
        return PIAttribute.model_validate(resp.json())

    def create_element(
        self,
        parent_web_id: str,
        name: str,
        description: str = "",
        template_name: str = "",
    ) -> None:
        """Create a child element under a parent element.

        Args:
            parent_web_id: WebID of the parent AF element.
            name: Name for the new element.
            description: Optional description.
            template_name: Optional AF element template name.

        Raises:
            NotFoundError: If the parent element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        body: dict[str, Any] = {"Name": name}
        if description:
            body["Description"] = description
        if template_name:
            body["TemplateName"] = template_name
        resp = self._client.post(
            f"/elements/{quote(parent_web_id, safe='')}/elements",
            json=body,
        )
        raise_for_response(resp)

    def create_attribute(
        self,
        element_web_id: str,
        name: str,
        *,
        description: str = "",
        type_qualifier: str = "",
        default_value: Any = None,
        config_string: str = "",
        is_configuration_item: bool = False,
    ) -> None:
        """Create a new AF attribute on an element.

        Calls ``POST /elements/{webId}/attributes``.

        Args:
            element_web_id: WebID of the parent AF element.
            name: Name for the new attribute.
            description: Optional description.
            type_qualifier: The PI AF value type, e.g. ``"Double"``,
                ``"String"``, ``"Int32"``. If omitted the server infers
                from ``default_value`` or uses ``"Double"``.
            default_value: Optional default value for the attribute.
            config_string: Optional data reference config string
                (e.g. a PI point reference like
                ``"\\\\SERVER\\sinusoid;ReadOnly=False"``).
            is_configuration_item: If ``True``, the attribute stores
                configuration data rather than time-series data.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        body: dict[str, Any] = {"Name": name}
        if description:
            body["Description"] = description
        if type_qualifier:
            body["TypeQualifier"] = type_qualifier
        if default_value is not None:
            body["DefaultValue"] = default_value
        if config_string:
            body["ConfigString"] = config_string
        if is_configuration_item:
            body["IsConfigurationItem"] = is_configuration_item
        resp = self._client.post(
            f"/elements/{quote(element_web_id, safe='')}/attributes",
            json=body,
        )
        raise_for_response(resp)

    def update_attribute(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an existing AF attribute.

        Sends a ``PATCH /attributes/{webId}`` request with the given body.
        Only include the fields you want to change (e.g.
        ``{"Description": "Updated desc"}``).

        Args:
            web_id: WebID of the AF attribute to update.
            body: Dictionary of attribute properties to update.  Keys use
                PI Web API PascalCase names (e.g. ``"Name"``,
                ``"Description"``, ``"DefaultValue"``, ``"ConfigString"``).

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.patch(
            f"/attributes/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def get_attribute_value(self, web_id: str) -> StreamValue:
        """Return the current value of an AF attribute.

        Calls ``GET /attributes/{webId}/value``.

        Args:
            web_id: WebID of the AF attribute.

        Returns:
            A :class:`StreamValue` with the current timestamped value.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            f"/attributes/{quote(web_id, safe='')}/value"
        )
        raise_for_response(resp)
        return StreamValue.model_validate(resp.json())

    def set_attribute_value(
        self,
        web_id: str,
        value: Any,
    ) -> None:
        """Set the value of an AF attribute.

        Calls ``PUT /attributes/{webId}/value``.

        Args:
            web_id: WebID of the AF attribute.
            value: The value to write.  For simple attributes pass a scalar
                (``42``, ``"hello"``).  For timestamped writes pass a dict
                matching the PI Web API ``TimedValue`` schema, e.g.
                ``{"Value": 42, "Timestamp": "2024-01-01T00:00:00Z"}``.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        body = value if isinstance(value, dict) else {"Value": value}
        resp = self._client.put(
            f"/attributes/{quote(web_id, safe='')}/value",
            json=body,
        )
        raise_for_response(resp)

    def update_element(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an existing AF element.

        Sends a ``PATCH /elements/{webId}`` request with the given body.
        Only include the fields you want to change.

        Args:
            web_id: WebID of the AF element to update.
            body: Dictionary of element properties to update.  Keys use
                PI Web API PascalCase names (e.g. ``"Name"``,
                ``"Description"``, ``"TemplateName"``).

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.patch(
            f"/elements/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete_attribute(self, web_id: str) -> None:
        """Delete an AF attribute.

        Args:
            web_id: WebID of the AF attribute to delete.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.delete(f"/attributes/{quote(web_id, safe='')}")
        raise_for_response(resp)

    def delete_element(self, web_id: str) -> None:
        """Delete an AF element.

        Args:
            web_id: WebID of the AF element to delete.

        Raises:
            NotFoundError: If no element with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.delete(f"/elements/{quote(web_id, safe='')}")
        raise_for_response(resp)


class AsyncElementsMixin:
    """Async methods for AF element and database lookup. Mixed into the async client class."""

    _client: httpx.AsyncClient

    async def get_asset_servers(self) -> list[PIAssetServer]:
        """Return all PI Asset Servers (AF Servers) registered with PI Web API.

        Returns:
            List of :class:`PIAssetServer` objects.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get("/assetservers")
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIAssetServer.model_validate(item) for item in items]

    async def get_asset_server(self, web_id: str) -> PIAssetServer:
        """Return a single PI Asset Server by its WebID.

        Args:
            web_id: WebID of the PI Asset Server.

        Returns:
            A :class:`PIAssetServer` populated from the API response.

        Raises:
            NotFoundError: If no asset server with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(f"/assetservers/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
        return PIAssetServer.model_validate(resp.json())

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
        search_full_hierarchy: bool = False,
    ) -> list[PIElement]:
        """Return AF elements in a database.

        By default only top-level (root) elements are returned.  Set
        ``search_full_hierarchy=True`` to traverse the entire element tree and
        return all matching elements at any depth.

        Args:
            database_web_id: WebID of the AF database.
            name_filter: Name pattern supporting wildcards. Defaults to ``"*"``.
            max_count: Maximum number of results to return. Defaults to ``100``.
            search_full_hierarchy: When ``True``, the PI Web API server searches
                recursively through all child elements.  Defaults to ``False``
                (top-level only).

        Returns:
            List of :class:`PIElement` objects.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: dict[str, str | int | bool] = {
            "nameFilter": name_filter,
            "maxCount": max_count,
        }
        if search_full_hierarchy:
            params["searchFullHierarchy"] = True
        resp = await self._client.get(
            f"/assetdatabases/{quote(database_web_id, safe='')}/elements",
            params=params,
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

    async def get_attribute_by_path(self, path: str) -> PIAttribute:
        """Look up an AF attribute by its full path.

        The path uses a pipe (``|``) to separate the element path from the
        attribute name, e.g. ``"\\\\AF_SERVER\\DB\\Element|Temperature"``.

        Args:
            path: Full AF attribute path.

        Returns:
            A :class:`PIAttribute` populated from the API response.

        Raises:
            NotFoundError: If the attribute path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get("/attributes", params={"path": path})
        await raise_for_response_async(resp)
        return PIAttribute.model_validate(resp.json())

    async def create_attribute(
        self,
        element_web_id: str,
        name: str,
        *,
        description: str = "",
        type_qualifier: str = "",
        default_value: Any = None,
        config_string: str = "",
        is_configuration_item: bool = False,
    ) -> None:
        """Create a new AF attribute on an element.

        Calls ``POST /elements/{webId}/attributes``.

        Args:
            element_web_id: WebID of the parent AF element.
            name: Name for the new attribute.
            description: Optional description.
            type_qualifier: The PI AF value type, e.g. ``"Double"``,
                ``"String"``, ``"Int32"``.
            default_value: Optional default value for the attribute.
            config_string: Optional data reference config string.
            is_configuration_item: If ``True``, the attribute stores
                configuration data rather than time-series data.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        body: dict[str, Any] = {"Name": name}
        if description:
            body["Description"] = description
        if type_qualifier:
            body["TypeQualifier"] = type_qualifier
        if default_value is not None:
            body["DefaultValue"] = default_value
        if config_string:
            body["ConfigString"] = config_string
        if is_configuration_item:
            body["IsConfigurationItem"] = is_configuration_item
        resp = await self._client.post(
            f"/elements/{quote(element_web_id, safe='')}/attributes",
            json=body,
        )
        await raise_for_response_async(resp)

    async def update_attribute(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an existing AF attribute.

        Sends a ``PATCH /attributes/{webId}`` request with the given body.

        Args:
            web_id: WebID of the AF attribute to update.
            body: Dictionary of attribute properties to update.  Keys use
                PI Web API PascalCase names (e.g. ``"Name"``,
                ``"Description"``, ``"DefaultValue"``).

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.patch(
            f"/attributes/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def get_attribute_value(self, web_id: str) -> StreamValue:
        """Return the current value of an AF attribute.

        Calls ``GET /attributes/{webId}/value``.

        Args:
            web_id: WebID of the AF attribute.

        Returns:
            A :class:`StreamValue` with the current timestamped value.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            f"/attributes/{quote(web_id, safe='')}/value"
        )
        await raise_for_response_async(resp)
        return StreamValue.model_validate(resp.json())

    async def set_attribute_value(
        self,
        web_id: str,
        value: Any,
    ) -> None:
        """Set the value of an AF attribute.

        Calls ``PUT /attributes/{webId}/value``.

        Args:
            web_id: WebID of the AF attribute.
            value: The value to write.  For simple attributes pass a scalar
                (``42``, ``"hello"``).  For timestamped writes pass a dict
                matching the PI Web API ``TimedValue`` schema, e.g.
                ``{"Value": 42, "Timestamp": "2024-01-01T00:00:00Z"}``.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        body = value if isinstance(value, dict) else {"Value": value}
        resp = await self._client.put(
            f"/attributes/{quote(web_id, safe='')}/value",
            json=body,
        )
        await raise_for_response_async(resp)

    async def update_element(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an existing AF element.

        Sends a ``PATCH /elements/{webId}`` request with the given body.

        Args:
            web_id: WebID of the AF element to update.
            body: Dictionary of element properties to update.  Keys use
                PI Web API PascalCase names (e.g. ``"Name"``,
                ``"Description"``, ``"TemplateName"``).

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.patch(
            f"/elements/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete_attribute(self, web_id: str) -> None:
        """Delete an AF attribute.

        Args:
            web_id: WebID of the AF attribute to delete.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.delete(f"/attributes/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)

    async def create_element(
        self,
        parent_web_id: str,
        name: str,
        description: str = "",
        template_name: str = "",
    ) -> None:
        """Create a child element under a parent element.

        Args:
            parent_web_id: WebID of the parent AF element.
            name: Name for the new element.
            description: Optional description.
            template_name: Optional AF element template name.

        Raises:
            NotFoundError: If the parent element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        body: dict[str, Any] = {"Name": name}
        if description:
            body["Description"] = description
        if template_name:
            body["TemplateName"] = template_name
        resp = await self._client.post(
            f"/elements/{quote(parent_web_id, safe='')}/elements",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete_element(self, web_id: str) -> None:
        """Delete an AF element.

        Args:
            web_id: WebID of the AF element to delete.

        Raises:
            NotFoundError: If no element with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.delete(f"/elements/{quote(web_id, safe='')}")
        await raise_for_response_async(resp)
