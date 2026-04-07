"""Attribute Template operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PIAttributeTemplate, PICategory

if TYPE_CHECKING:
    import httpx


class AttributeTemplatesMixin:
    """Methods for Attribute Template operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_web_id(self, web_id: str) -> PIAttributeTemplate:
        """Look up an Attribute Template by its WebID.

        Calls ``GET /attributetemplates/{webId}``.

        Args:
            web_id: WebID of the attribute template.

        Returns:
            A :class:`PIAttributeTemplate` populated from the API response.

        Raises:
            NotFoundError: If no attribute template with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/attributetemplates/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)
        return PIAttributeTemplate.model_validate(resp.json())

    def get_by_path(self, path: str) -> PIAttributeTemplate:
        """Look up an Attribute Template by its full path.

        Calls ``GET /attributetemplates`` with a ``path`` query parameter.

        Args:
            path: Full AF path to the attribute template, e.g.
                ``"\\\\AF_SERVER\\DB\\ElementTemplates[Pump]``
                ``|AttributeTemplates[Temperature]"``.

        Returns:
            A :class:`PIAttributeTemplate` populated from the API response.

        Raises:
            NotFoundError: If no attribute template exists at the path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            "/attributetemplates", params={"path": path}
        )
        raise_for_response(resp)
        return PIAttributeTemplate.model_validate(resp.json())

    def get_attribute_templates(
        self,
        web_id: str,
    ) -> list[PIAttributeTemplate]:
        """List child attribute templates under a parent attribute template.

        Calls ``GET /attributetemplates/{webId}/attributetemplates``.

        Args:
            web_id: WebID of the parent attribute template.

        Returns:
            A list of :class:`PIAttributeTemplate` child objects.

        Raises:
            NotFoundError: If the attribute template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/attributetemplates/{quote(web_id, safe='')}"
            "/attributetemplates"
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", data) if isinstance(data, dict) else data
        )
        return [PIAttributeTemplate.model_validate(item) for item in items]

    def get_categories(
        self,
        web_id: str,
    ) -> list[PICategory]:
        """List categories assigned to an attribute template.

        Calls ``GET /attributetemplates/{webId}/categories``.

        Args:
            web_id: WebID of the attribute template.

        Returns:
            A list of :class:`PICategory` objects.

        Raises:
            NotFoundError: If the attribute template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/attributetemplates/{quote(web_id, safe='')}/categories"
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", data) if isinstance(data, dict) else data
        )
        return [PICategory.model_validate(item) for item in items]

    def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an Attribute Template.

        Calls ``PATCH /attributetemplates/{webId}``.

        Args:
            web_id: WebID of the attribute template.
            body: Fields to update (e.g. ``{"Description": "new desc"}``).

        Raises:
            NotFoundError: If the attribute template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"/attributetemplates/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete an Attribute Template.

        Calls ``DELETE /attributetemplates/{webId}``.

        Caution: deleting an attribute template removes the corresponding
        attribute from all elements derived from the parent element template.

        Args:
            web_id: WebID of the attribute template.

        Raises:
            NotFoundError: If the attribute template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/attributetemplates/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncAttributeTemplatesMixin:
    """Async methods for Attribute Template operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(self, web_id: str) -> PIAttributeTemplate:
        """Look up an Attribute Template by its WebID.

        Calls ``GET /attributetemplates/{webId}``.

        Args:
            web_id: WebID of the attribute template.

        Returns:
            A :class:`PIAttributeTemplate` populated from the API response.

        Raises:
            NotFoundError: If no attribute template with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/attributetemplates/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
        return PIAttributeTemplate.model_validate(resp.json())

    async def get_by_path(self, path: str) -> PIAttributeTemplate:
        """Look up an Attribute Template by its full path.

        Calls ``GET /attributetemplates`` with a ``path`` query parameter.

        Args:
            path: Full AF path to the attribute template.

        Returns:
            A :class:`PIAttributeTemplate` populated from the API response.

        Raises:
            NotFoundError: If no attribute template exists at the path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            "/attributetemplates", params={"path": path}
        )
        await raise_for_response_async(resp)
        return PIAttributeTemplate.model_validate(resp.json())

    async def get_attribute_templates(
        self,
        web_id: str,
    ) -> list[PIAttributeTemplate]:
        """List child attribute templates under a parent attribute template.

        Calls ``GET /attributetemplates/{webId}/attributetemplates``.

        Args:
            web_id: WebID of the parent attribute template.

        Returns:
            A list of :class:`PIAttributeTemplate` child objects.

        Raises:
            NotFoundError: If the attribute template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/attributetemplates/{quote(web_id, safe='')}"
            "/attributetemplates"
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", data) if isinstance(data, dict) else data
        )
        return [PIAttributeTemplate.model_validate(item) for item in items]

    async def get_categories(
        self,
        web_id: str,
    ) -> list[PICategory]:
        """List categories assigned to an attribute template.

        Calls ``GET /attributetemplates/{webId}/categories``.

        Args:
            web_id: WebID of the attribute template.

        Returns:
            A list of :class:`PICategory` objects.

        Raises:
            NotFoundError: If the attribute template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/attributetemplates/{quote(web_id, safe='')}/categories"
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", data) if isinstance(data, dict) else data
        )
        return [PICategory.model_validate(item) for item in items]

    async def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an Attribute Template.

        Calls ``PATCH /attributetemplates/{webId}``.

        Args:
            web_id: WebID of the attribute template.
            body: Fields to update (e.g. ``{"Description": "new desc"}``).

        Raises:
            NotFoundError: If the attribute template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"/attributetemplates/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete an Attribute Template.

        Calls ``DELETE /attributetemplates/{webId}``.

        Caution: deleting an attribute template removes the corresponding
        attribute from all elements derived from the parent element template.

        Args:
            web_id: WebID of the attribute template.

        Raises:
            NotFoundError: If the attribute template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/attributetemplates/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
