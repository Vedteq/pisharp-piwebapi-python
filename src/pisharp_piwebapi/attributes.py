"""Standalone Attribute operations for PI Web API.

Provides direct CRUD on AF Attributes by WebID, including the critical
``GET /attributes/{webId}/value`` and ``PUT /attributes/{webId}/value``
endpoints for reading and writing a single attribute's current value.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PIAttribute, StreamValue

if TYPE_CHECKING:
    import httpx


class AttributesMixin:
    """Methods for standalone AF Attribute operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_web_id(self, web_id: str) -> PIAttribute:
        """Look up an AF Attribute by its WebID.

        Calls ``GET /attributes/{webId}``.

        Args:
            web_id: WebID of the attribute.

        Returns:
            A :class:`PIAttribute` populated from the API response.

        Raises:
            NotFoundError: If no attribute with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(f"/attributes/{quote(web_id, safe='')}")
        raise_for_response(resp)
        return PIAttribute.model_validate(resp.json())

    def get_by_path(self, path: str) -> PIAttribute:
        """Look up an AF Attribute by its full AF path.

        Calls ``GET /attributes`` with a ``path`` query parameter.

        Args:
            path: Full AF attribute path, e.g.
                ``"\\\\AF_SERVER\\DB\\Element|Attribute"``.

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

    def get_value(self, web_id: str) -> StreamValue:
        """Read the current value of an attribute.

        Calls ``GET /attributes/{webId}/value``.  This is one of the
        most frequently used PI Web API endpoints.

        Args:
            web_id: WebID of the attribute.

        Returns:
            A :class:`StreamValue` with the current value and timestamp.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/attributes/{quote(web_id, safe='')}/value"
        )
        raise_for_response(resp)
        return StreamValue.model_validate(resp.json())

    def set_value(
        self,
        web_id: str,
        value: Any,
        *,
        timestamp: str | datetime | None = None,
    ) -> None:
        """Write a value to an attribute.

        Calls ``PUT /attributes/{webId}/value``.

        Args:
            web_id: WebID of the attribute.
            value: The value to write.
            timestamp: Optional timestamp for the value.  When ``None``,
                the server uses the current time.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = {"Value": value}
        if timestamp is not None:
            body["Timestamp"] = (
                timestamp.isoformat()
                if isinstance(timestamp, datetime)
                else timestamp
            )
        resp = self._client.put(
            f"/attributes/{quote(web_id, safe='')}/value",
            json=body,
        )
        raise_for_response(resp)

    def update(
        self,
        web_id: str,
        *,
        description: str | None = None,
        config_string: str | None = None,
        is_configuration_item: bool | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        """Update an attribute's properties.

        Calls ``PATCH /attributes/{webId}``.

        Args:
            web_id: WebID of the attribute to update.
            description: New description.
            config_string: New config string (data reference).
            is_configuration_item: Whether this is a configuration item.
            extra_fields: Additional fields to include in the request body.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = dict(extra_fields) if extra_fields else {}
        if description is not None:
            body["Description"] = description
        if config_string is not None:
            body["ConfigString"] = config_string
        if is_configuration_item is not None:
            body["IsConfigurationItem"] = is_configuration_item
        if not body:
            return
        resp = self._client.patch(
            f"/attributes/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def get_children(
        self,
        web_id: str,
        *,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIAttribute]:
        """List child (nested) attributes of an attribute.

        Calls ``GET /attributes/{webId}/attributes``.  Child attributes
        are common in AF for limits (High, Low, Target) and other
        compound attribute structures.

        Args:
            web_id: WebID of the parent attribute.
            name_filter: Name pattern. Defaults to ``"*"`` (all).
            max_count: Maximum results. Defaults to ``100``.

        Returns:
            List of :class:`PIAttribute` child objects.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/attributes/{quote(web_id, safe='')}/attributes",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIAttribute.model_validate(item) for item in items]

    def delete(self, web_id: str) -> None:
        """Delete an attribute.

        Calls ``DELETE /attributes/{webId}``.

        Args:
            web_id: WebID of the attribute to delete.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(f"/attributes/{quote(web_id, safe='')}")
        raise_for_response(resp)


class AsyncAttributesMixin:
    """Async methods for standalone AF Attribute operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(self, web_id: str) -> PIAttribute:
        """Look up an AF Attribute by its WebID.

        Calls ``GET /attributes/{webId}``.

        Args:
            web_id: WebID of the attribute.

        Returns:
            A :class:`PIAttribute` populated from the API response.

        Raises:
            NotFoundError: If no attribute with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/attributes/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
        return PIAttribute.model_validate(resp.json())

    async def get_by_path(self, path: str) -> PIAttribute:
        """Look up an AF Attribute by its full AF path.

        Calls ``GET /attributes`` with a ``path`` query parameter.

        Args:
            path: Full AF attribute path.

        Returns:
            A :class:`PIAttribute` populated from the API response.

        Raises:
            NotFoundError: If the attribute path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            "/attributes", params={"path": path}
        )
        await raise_for_response_async(resp)
        return PIAttribute.model_validate(resp.json())

    async def get_value(self, web_id: str) -> StreamValue:
        """Read the current value of an attribute.

        Calls ``GET /attributes/{webId}/value``.

        Args:
            web_id: WebID of the attribute.

        Returns:
            A :class:`StreamValue` with the current value and timestamp.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/attributes/{quote(web_id, safe='')}/value"
        )
        await raise_for_response_async(resp)
        return StreamValue.model_validate(resp.json())

    async def set_value(
        self,
        web_id: str,
        value: Any,
        *,
        timestamp: str | datetime | None = None,
    ) -> None:
        """Write a value to an attribute.

        Calls ``PUT /attributes/{webId}/value``.

        Args:
            web_id: WebID of the attribute.
            value: The value to write.
            timestamp: Optional timestamp for the value.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = {"Value": value}
        if timestamp is not None:
            body["Timestamp"] = (
                timestamp.isoformat()
                if isinstance(timestamp, datetime)
                else timestamp
            )
        resp = await self._client.put(
            f"/attributes/{quote(web_id, safe='')}/value",
            json=body,
        )
        await raise_for_response_async(resp)

    async def update(
        self,
        web_id: str,
        *,
        description: str | None = None,
        config_string: str | None = None,
        is_configuration_item: bool | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        """Update an attribute's properties.

        Calls ``PATCH /attributes/{webId}``.

        Args:
            web_id: WebID of the attribute to update.
            description: New description.
            config_string: New config string (data reference).
            is_configuration_item: Whether this is a configuration item.
            extra_fields: Additional fields to include in the request body.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = dict(extra_fields) if extra_fields else {}
        if description is not None:
            body["Description"] = description
        if config_string is not None:
            body["ConfigString"] = config_string
        if is_configuration_item is not None:
            body["IsConfigurationItem"] = is_configuration_item
        if not body:
            return
        resp = await self._client.patch(
            f"/attributes/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def get_children(
        self,
        web_id: str,
        *,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIAttribute]:
        """List child (nested) attributes of an attribute.

        Calls ``GET /attributes/{webId}/attributes``.

        Args:
            web_id: WebID of the parent attribute.
            name_filter: Name pattern. Defaults to ``"*"`` (all).
            max_count: Maximum results. Defaults to ``100``.

        Returns:
            List of :class:`PIAttribute` child objects.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/attributes/{quote(web_id, safe='')}/attributes",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [PIAttribute.model_validate(item) for item in items]

    async def delete(self, web_id: str) -> None:
        """Delete an attribute.

        Calls ``DELETE /attributes/{webId}``.

        Args:
            web_id: WebID of the attribute to delete.

        Raises:
            NotFoundError: If the attribute WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/attributes/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
