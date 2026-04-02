"""System controller operations for PI Web API.

Provides health checks, user identity verification, and version
information via the ``/system`` endpoints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pisharp_piwebapi.exceptions import raise_for_response, raise_for_response_async
from pisharp_piwebapi.models import PISystemStatus, PIUserInfo, PIVersions

if TYPE_CHECKING:
    import httpx


class SystemMixin:
    """Methods for PI Web API system operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_status(self) -> PISystemStatus:
        """Return the PI Web API system status.

        Calls ``GET /system/status``.  Useful as a health check to verify
        that PI Web API is running and can reach its backend servers.

        Returns:
            A :class:`PISystemStatus` with uptime and server state.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/system/status")
        raise_for_response(resp)
        return PISystemStatus.model_validate(resp.json())

    def get_user_info(self) -> PIUserInfo:
        """Return information about the authenticated user.

        Calls ``GET /system/userinfo``.  This is the best way to verify
        that authentication (especially Kerberos delegation) is working
        correctly.

        Returns:
            A :class:`PIUserInfo` with the resolved identity name and
            impersonation level.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/system/userinfo")
        raise_for_response(resp)
        return PIUserInfo.model_validate(resp.json())

    def get_versions(self) -> PIVersions:
        """Return version information for PI Web API and its dependencies.

        Calls ``GET /system/versions``.

        Returns:
            A :class:`PIVersions` mapping component names to version strings.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/system/versions")
        raise_for_response(resp)
        return PIVersions.model_validate(resp.json())


class AsyncSystemMixin:
    """Async methods for PI Web API system operations."""

    _client: httpx.AsyncClient

    async def get_status(self) -> PISystemStatus:
        """Return the PI Web API system status.

        Calls ``GET /system/status``.

        Returns:
            A :class:`PISystemStatus` with uptime and server state.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get("/system/status")
        await raise_for_response_async(resp)
        return PISystemStatus.model_validate(resp.json())

    async def get_user_info(self) -> PIUserInfo:
        """Return information about the authenticated user.

        Calls ``GET /system/userinfo``.

        Returns:
            A :class:`PIUserInfo` with the resolved identity name.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get("/system/userinfo")
        await raise_for_response_async(resp)
        return PIUserInfo.model_validate(resp.json())

    async def get_versions(self) -> PIVersions:
        """Return version information for PI Web API and its dependencies.

        Calls ``GET /system/versions``.

        Returns:
            A :class:`PIVersions` mapping component names to version strings.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get("/system/versions")
        await raise_for_response_async(resp)
        return PIVersions.model_validate(resp.json())
