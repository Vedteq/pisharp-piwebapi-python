"""PI Security Mapping operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PISecurityMapping

if TYPE_CHECKING:
    import httpx


class SecurityMappingsMixin:
    """Methods for PI Security Mapping operations. Mixed into the sync client.

    Security mappings associate Windows identities (users or groups)
    with PI security identities, controlling which Windows accounts
    receive which PI security identity when connecting to the PI Data
    Archive.
    """

    _client: httpx.Client

    def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> PISecurityMapping:
        """Look up a Security Mapping by its WebID.

        Calls ``GET /securitymappings/{webId}``.

        Args:
            web_id: WebID of the security mapping.
            selected_fields: Comma-separated list of fields to include
                in the response.

        Returns:
            A :class:`PISecurityMapping` populated from the API response.

        Raises:
            NotFoundError: If no security mapping with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            f"/securitymappings/{quote(web_id, safe='')}",
            params=params or None,
        )
        raise_for_response(resp)
        return PISecurityMapping.model_validate(resp.json())

    def get_by_path(self, path: str) -> PISecurityMapping:
        """Look up a Security Mapping by its full path.

        Calls ``GET /securitymappings`` with a ``path`` query parameter.

        Args:
            path: Full path to the security mapping, e.g.
                ``"\\\\PISERVER\\Security Mappings[Mapping1]"``.

        Returns:
            A :class:`PISecurityMapping` populated from the API response.

        Raises:
            NotFoundError: If no security mapping exists at the given path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            "/securitymappings", params={"path": path}
        )
        raise_for_response(resp)
        return PISecurityMapping.model_validate(resp.json())

    def list_by_server(
        self,
        data_server_web_id: str,
        *,
        max_count: int = 100,
        field: str = "Name",
        sort_order: str = "Ascending",
    ) -> list[PISecurityMapping]:
        """List security mappings on a PI Data Server.

        Calls ``GET /dataservers/{webId}/securitymappings``.

        Args:
            data_server_web_id: WebID of the PI Data Server.
            max_count: Maximum number of results. Defaults to ``100``.
            field: Sort field. Defaults to ``"Name"``.
            sort_order: ``"Ascending"`` or ``"Descending"``.

        Returns:
            List of :class:`PISecurityMapping` objects.

        Raises:
            NotFoundError: If the data server WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(data_server_web_id, "data_server_web_id")
        resp = self._client.get(
            f"/dataservers/{quote(data_server_web_id, safe='')}"
            "/securitymappings",
            params={
                "maxCount": max_count,
                "field": field,
                "sortOrder": sort_order,
            },
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", data) if isinstance(data, dict) else data
        )
        return [PISecurityMapping.model_validate(i) for i in items]

    def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a Security Mapping.

        Calls ``PATCH /securitymappings/{webId}``.

        Args:
            web_id: WebID of the security mapping.
            body: Fields to update (e.g.
                ``{"Description": "updated", "Account": "DOMAIN\\\\Group"}``).

        Raises:
            NotFoundError: If the security mapping WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"/securitymappings/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete a Security Mapping.

        Calls ``DELETE /securitymappings/{webId}``.

        Args:
            web_id: WebID of the security mapping.

        Raises:
            NotFoundError: If the security mapping WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/securitymappings/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncSecurityMappingsMixin:
    """Async methods for PI Security Mapping operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> PISecurityMapping:
        """Look up a Security Mapping by its WebID.

        Calls ``GET /securitymappings/{webId}``.

        Args:
            web_id: WebID of the security mapping.
            selected_fields: Comma-separated list of fields to include
                in the response.

        Returns:
            A :class:`PISecurityMapping` populated from the API response.

        Raises:
            NotFoundError: If no security mapping with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            f"/securitymappings/{quote(web_id, safe='')}",
            params=params or None,
        )
        await raise_for_response_async(resp)
        return PISecurityMapping.model_validate(resp.json())

    async def get_by_path(self, path: str) -> PISecurityMapping:
        """Look up a Security Mapping by its full path.

        Calls ``GET /securitymappings`` with a ``path`` query parameter.

        Args:
            path: Full path to the security mapping.

        Returns:
            A :class:`PISecurityMapping` populated from the API response.

        Raises:
            NotFoundError: If no security mapping exists at the given path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            "/securitymappings", params={"path": path}
        )
        await raise_for_response_async(resp)
        return PISecurityMapping.model_validate(resp.json())

    async def list_by_server(
        self,
        data_server_web_id: str,
        *,
        max_count: int = 100,
        field: str = "Name",
        sort_order: str = "Ascending",
    ) -> list[PISecurityMapping]:
        """List security mappings on a PI Data Server.

        Calls ``GET /dataservers/{webId}/securitymappings``.

        Args:
            data_server_web_id: WebID of the PI Data Server.
            max_count: Maximum number of results. Defaults to ``100``.
            field: Sort field. Defaults to ``"Name"``.
            sort_order: ``"Ascending"`` or ``"Descending"``.

        Returns:
            List of :class:`PISecurityMapping` objects.

        Raises:
            NotFoundError: If the data server WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(data_server_web_id, "data_server_web_id")
        resp = await self._client.get(
            f"/dataservers/{quote(data_server_web_id, safe='')}"
            "/securitymappings",
            params={
                "maxCount": max_count,
                "field": field,
                "sortOrder": sort_order,
            },
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", data) if isinstance(data, dict) else data
        )
        return [PISecurityMapping.model_validate(i) for i in items]

    async def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a Security Mapping.

        Calls ``PATCH /securitymappings/{webId}``.

        Args:
            web_id: WebID of the security mapping.
            body: Fields to update.

        Raises:
            NotFoundError: If the security mapping WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"/securitymappings/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete a Security Mapping.

        Calls ``DELETE /securitymappings/{webId}``.

        Args:
            web_id: WebID of the security mapping.

        Raises:
            NotFoundError: If the security mapping WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/securitymappings/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
