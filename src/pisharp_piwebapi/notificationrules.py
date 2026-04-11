"""AF Notification Rule operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PINotificationRule, PINotificationRuleSubscriber

if TYPE_CHECKING:
    import httpx


class NotificationRulesMixin:
    """Methods for AF Notification Rule operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_web_id(self, web_id: str) -> PINotificationRule:
        """Look up an AF Notification Rule by its WebID.

        Calls ``GET /notificationrules/{webId}``.

        Args:
            web_id: WebID of the notification rule.

        Returns:
            A :class:`PINotificationRule` populated from the API response.

        Raises:
            NotFoundError: If no notification rule with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/notificationrules/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)
        return PINotificationRule.model_validate(resp.json())

    def get_by_path(self, path: str) -> PINotificationRule:
        """Look up an AF Notification Rule by its full path.

        Calls ``GET /notificationrules`` with a ``path`` query parameter.

        Args:
            path: Full AF notification rule path, e.g.
                ``"\\\\AF_SERVER\\DB\\Element|NotificationRule"``.

        Returns:
            A :class:`PINotificationRule` populated from the API response.

        Raises:
            NotFoundError: If the notification rule path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            "/notificationrules", params={"path": path}
        )
        raise_for_response(resp)
        return PINotificationRule.model_validate(resp.json())

    def get_by_element(
        self,
        element_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PINotificationRule]:
        """List notification rules on an element.

        Calls ``GET /elements/{webId}/notificationrules``.

        Args:
            element_web_id: WebID of the AF element.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all rules).
            max_count: Maximum number of results. Defaults to ``100``.

        Returns:
            List of :class:`PINotificationRule` objects.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(element_web_id, "element_web_id")
        resp = self._client.get(
            f"/elements/{quote(element_web_id, safe='')}/notificationrules",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PINotificationRule.model_validate(item) for item in items]

    def get_subscribers(
        self,
        web_id: str,
    ) -> list[PINotificationRuleSubscriber]:
        """List subscribers (delivery contacts) for a notification rule.

        Calls ``GET /notificationrules/{webId}/notificationrulesubscribers``.

        Args:
            web_id: WebID of the notification rule.

        Returns:
            List of :class:`PINotificationRuleSubscriber` objects.

        Raises:
            NotFoundError: If the notification rule WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/notificationrules/{quote(web_id, safe='')}"
            "/notificationrulesubscribers",
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [
            PINotificationRuleSubscriber.model_validate(item)
            for item in items
        ]

    def delete(self, web_id: str) -> None:
        """Delete an AF Notification Rule.

        Calls ``DELETE /notificationrules/{webId}``.

        Args:
            web_id: WebID of the notification rule to delete.

        Raises:
            NotFoundError: If no notification rule with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/notificationrules/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncNotificationRulesMixin:
    """Async methods for AF Notification Rule operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(self, web_id: str) -> PINotificationRule:
        """Look up an AF Notification Rule by its WebID.

        Calls ``GET /notificationrules/{webId}``.

        Args:
            web_id: WebID of the notification rule.

        Returns:
            A :class:`PINotificationRule` populated from the API response.

        Raises:
            NotFoundError: If no notification rule with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/notificationrules/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
        return PINotificationRule.model_validate(resp.json())

    async def get_by_path(self, path: str) -> PINotificationRule:
        """Look up an AF Notification Rule by its full path.

        Calls ``GET /notificationrules`` with a ``path`` query parameter.

        Args:
            path: Full AF notification rule path.

        Returns:
            A :class:`PINotificationRule` populated from the API response.

        Raises:
            NotFoundError: If the notification rule path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            "/notificationrules", params={"path": path}
        )
        await raise_for_response_async(resp)
        return PINotificationRule.model_validate(resp.json())

    async def get_by_element(
        self,
        element_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PINotificationRule]:
        """List notification rules on an element.

        Calls ``GET /elements/{webId}/notificationrules``.

        Args:
            element_web_id: WebID of the AF element.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all rules).
            max_count: Maximum number of results. Defaults to ``100``.

        Returns:
            List of :class:`PINotificationRule` objects.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(element_web_id, "element_web_id")
        resp = await self._client.get(
            f"/elements/{quote(element_web_id, safe='')}/notificationrules",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PINotificationRule.model_validate(item) for item in items]

    async def get_subscribers(
        self,
        web_id: str,
    ) -> list[PINotificationRuleSubscriber]:
        """List subscribers (delivery contacts) for a notification rule.

        Calls ``GET /notificationrules/{webId}/notificationrulesubscribers``.

        Args:
            web_id: WebID of the notification rule.

        Returns:
            List of :class:`PINotificationRuleSubscriber` objects.

        Raises:
            NotFoundError: If the notification rule WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/notificationrules/{quote(web_id, safe='')}"
            "/notificationrulesubscribers",
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [
            PINotificationRuleSubscriber.model_validate(item)
            for item in items
        ]

    async def delete(self, web_id: str) -> None:
        """Delete an AF Notification Rule.

        Calls ``DELETE /notificationrules/{webId}``.

        Args:
            web_id: WebID of the notification rule to delete.

        Raises:
            NotFoundError: If no notification rule with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/notificationrules/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
