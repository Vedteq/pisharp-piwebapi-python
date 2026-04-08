"""PI Security Identity operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PISecurityIdentity

if TYPE_CHECKING:
    import httpx


class SecurityIdentitiesMixin:
    """Methods for PI Security Identity operations. Mixed into the sync client.

    PI Security Identities are the principal objects used by the PI Data
    Archive for access control.  They map to Windows users/groups via
    security mappings.
    """

    _client: httpx.Client

    def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> PISecurityIdentity:
        """Look up a Security Identity by its WebID.

        Calls ``GET /securityidentities/{webId}``.

        Args:
            web_id: WebID of the security identity.
            selected_fields: Comma-separated list of fields to include
                in the response.

        Returns:
            A :class:`PISecurityIdentity` populated from the API response.

        Raises:
            NotFoundError: If no security identity with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            f"/securityidentities/{quote(web_id, safe='')}",
            params=params or None,
        )
        raise_for_response(resp)
        return PISecurityIdentity.model_validate(resp.json())

    def get_by_path(self, path: str) -> PISecurityIdentity:
        """Look up a Security Identity by its full path.

        Calls ``GET /securityidentities`` with a ``path`` query parameter.

        Args:
            path: Full path to the security identity, e.g.
                ``"\\\\PISERVER\\Security Identities[piworld]"``.

        Returns:
            A :class:`PISecurityIdentity` populated from the API response.

        Raises:
            NotFoundError: If no security identity exists at the given path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            "/securityidentities", params={"path": path}
        )
        raise_for_response(resp)
        return PISecurityIdentity.model_validate(resp.json())

    def get_by_name(
        self,
        data_server_web_id: str,
        name: str,
    ) -> PISecurityIdentity:
        """Look up a Security Identity by name on a Data Server.

        Calls ``GET /dataservers/{webId}/securityidentities``
        with a ``name`` query parameter.

        Args:
            data_server_web_id: WebID of the PI Data Server.
            name: Exact name of the security identity.

        Returns:
            A :class:`PISecurityIdentity` populated from the API response.

        Raises:
            NotFoundError: If no security identity with the given name
                exists on the server.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(data_server_web_id, "data_server_web_id")
        resp = self._client.get(
            f"/dataservers/{quote(data_server_web_id, safe='')}"
            "/securityidentities",
            params={"name": name},
        )
        raise_for_response(resp)
        return PISecurityIdentity.model_validate(resp.json())

    def list_by_server(
        self,
        data_server_web_id: str,
        *,
        max_count: int = 100,
        field: str = "Name",
        sort_order: str = "Ascending",
    ) -> list[PISecurityIdentity]:
        """List security identities on a PI Data Server.

        Calls ``GET /dataservers/{webId}/securityidentities``.

        Args:
            data_server_web_id: WebID of the PI Data Server.
            max_count: Maximum number of results. Defaults to ``100``.
            field: Sort field. Defaults to ``"Name"``.
            sort_order: ``"Ascending"`` or ``"Descending"``.

        Returns:
            List of :class:`PISecurityIdentity` objects.

        Raises:
            NotFoundError: If the data server WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(data_server_web_id, "data_server_web_id")
        resp = self._client.get(
            f"/dataservers/{quote(data_server_web_id, safe='')}"
            "/securityidentities",
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
        return [PISecurityIdentity.model_validate(i) for i in items]

    def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a Security Identity.

        Calls ``PATCH /securityidentities/{webId}``.

        Args:
            web_id: WebID of the security identity.
            body: Fields to update (e.g.
                ``{"Description": "updated", "IsEnabled": False}``).

        Raises:
            NotFoundError: If the security identity WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"/securityidentities/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete a Security Identity.

        Calls ``DELETE /securityidentities/{webId}``.

        Args:
            web_id: WebID of the security identity.

        Raises:
            NotFoundError: If the security identity WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/securityidentities/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncSecurityIdentitiesMixin:
    """Async methods for PI Security Identity operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> PISecurityIdentity:
        """Look up a Security Identity by its WebID.

        Calls ``GET /securityidentities/{webId}``.

        Args:
            web_id: WebID of the security identity.
            selected_fields: Comma-separated list of fields to include
                in the response.

        Returns:
            A :class:`PISecurityIdentity` populated from the API response.

        Raises:
            NotFoundError: If no security identity with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            f"/securityidentities/{quote(web_id, safe='')}",
            params=params or None,
        )
        await raise_for_response_async(resp)
        return PISecurityIdentity.model_validate(resp.json())

    async def get_by_path(self, path: str) -> PISecurityIdentity:
        """Look up a Security Identity by its full path.

        Calls ``GET /securityidentities`` with a ``path`` query parameter.

        Args:
            path: Full path to the security identity.

        Returns:
            A :class:`PISecurityIdentity` populated from the API response.

        Raises:
            NotFoundError: If no security identity exists at the given path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            "/securityidentities", params={"path": path}
        )
        await raise_for_response_async(resp)
        return PISecurityIdentity.model_validate(resp.json())

    async def get_by_name(
        self,
        data_server_web_id: str,
        name: str,
    ) -> PISecurityIdentity:
        """Look up a Security Identity by name on a Data Server.

        Calls ``GET /dataservers/{webId}/securityidentities``
        with a ``name`` query parameter.

        Args:
            data_server_web_id: WebID of the PI Data Server.
            name: Exact name of the security identity.

        Returns:
            A :class:`PISecurityIdentity` populated from the API response.

        Raises:
            NotFoundError: If no security identity with the given name
                exists on the server.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(data_server_web_id, "data_server_web_id")
        resp = await self._client.get(
            f"/dataservers/{quote(data_server_web_id, safe='')}"
            "/securityidentities",
            params={"name": name},
        )
        await raise_for_response_async(resp)
        return PISecurityIdentity.model_validate(resp.json())

    async def list_by_server(
        self,
        data_server_web_id: str,
        *,
        max_count: int = 100,
        field: str = "Name",
        sort_order: str = "Ascending",
    ) -> list[PISecurityIdentity]:
        """List security identities on a PI Data Server.

        Calls ``GET /dataservers/{webId}/securityidentities``.

        Args:
            data_server_web_id: WebID of the PI Data Server.
            max_count: Maximum number of results. Defaults to ``100``.
            field: Sort field. Defaults to ``"Name"``.
            sort_order: ``"Ascending"`` or ``"Descending"``.

        Returns:
            List of :class:`PISecurityIdentity` objects.

        Raises:
            NotFoundError: If the data server WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(data_server_web_id, "data_server_web_id")
        resp = await self._client.get(
            f"/dataservers/{quote(data_server_web_id, safe='')}"
            "/securityidentities",
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
        return [PISecurityIdentity.model_validate(i) for i in items]

    async def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a Security Identity.

        Calls ``PATCH /securityidentities/{webId}``.

        Args:
            web_id: WebID of the security identity.
            body: Fields to update (e.g.
                ``{"Description": "updated", "IsEnabled": False}``).

        Raises:
            NotFoundError: If the security identity WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"/securityidentities/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete a Security Identity.

        Calls ``DELETE /securityidentities/{webId}``.

        Args:
            web_id: WebID of the security identity.

        Raises:
            NotFoundError: If the security identity WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/securityidentities/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
