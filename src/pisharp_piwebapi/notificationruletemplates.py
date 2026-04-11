"""AF Notification Rule Template operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import (
    PINotificationRuleSubscriber,
    PINotificationRuleTemplate,
)

if TYPE_CHECKING:
    import httpx


class NotificationRuleTemplatesMixin:
    """Methods for AF Notification Rule Template operations.

    Mixed into the sync client.
    """

    _client: httpx.Client

    def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> PINotificationRuleTemplate:
        """Look up an AF Notification Rule Template by its WebID.

        Calls ``GET /notificationruletemplates/{webId}``.

        Args:
            web_id: WebID of the notification rule template.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            A :class:`PINotificationRuleTemplate` populated from the API
            response.

        Raises:
            NotFoundError: If no template with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            f"/notificationruletemplates/{quote(web_id, safe='')}",
            params=params,
        )
        raise_for_response(resp)
        return PINotificationRuleTemplate.model_validate(resp.json())

    def get_by_path(
        self,
        path: str,
        *,
        selected_fields: str | None = None,
    ) -> PINotificationRuleTemplate:
        """Look up an AF Notification Rule Template by its full path.

        Calls ``GET /notificationruletemplates`` with a ``path`` query
        parameter.

        Args:
            path: Full AF notification rule template path, e.g.
                ``"\\\\AF_SERVER\\DB\\NotificationRuleTemplates[Name]"``.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            A :class:`PINotificationRuleTemplate` populated from the API
            response.

        Raises:
            NotFoundError: If the template path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: dict[str, Any] = {"path": path}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = self._client.get("/notificationruletemplates", params=params)
        raise_for_response(resp)
        return PINotificationRuleTemplate.model_validate(resp.json())

    def get_by_database(
        self,
        database_web_id: str,
        *,
        name_filter: str = "*",
        max_count: int = 100,
        selected_fields: str | None = None,
    ) -> list[PINotificationRuleTemplate]:
        """List notification rule templates in an AF database.

        Calls ``GET /assetdatabases/{webId}/notificationruletemplates``.

        Args:
            database_web_id: WebID of the AF database.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all templates).
            max_count: Maximum number of results. Defaults to ``100``.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            List of :class:`PINotificationRuleTemplate` objects.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(database_web_id, "database_web_id")
        params: dict[str, Any] = {
            "nameFilter": name_filter,
            "maxCount": max_count,
        }
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            f"/assetdatabases/{quote(database_web_id, safe='')}"
            "/notificationruletemplates",
            params=params,
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [PINotificationRuleTemplate.model_validate(item) for item in items]

    def create_on_database(
        self,
        database_web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Create a notification rule template on an AF database.

        Calls ``POST /assetdatabases/{webId}/notificationruletemplates``.

        Args:
            database_web_id: WebID of the parent AF database.
            body: Template definition (Name, Description, Criteria,
                ResendInterval, etc.).

        Raises:
            NotFoundError: If the database WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(database_web_id, "database_web_id")
        resp = self._client.post(
            f"/assetdatabases/{quote(database_web_id, safe='')}"
            "/notificationruletemplates",
            json=body,
        )
        raise_for_response(resp)

    def get_subscribers(
        self,
        web_id: str,
    ) -> list[PINotificationRuleSubscriber]:
        """List subscribers for a notification rule template.

        Calls ``GET /notificationruletemplates/{webId}``
        ``/notificationrulesubscribers``.

        Args:
            web_id: WebID of the notification rule template.

        Returns:
            List of :class:`PINotificationRuleSubscriber` objects.

        Raises:
            NotFoundError: If the template WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/notificationruletemplates/{quote(web_id, safe='')}"
            "/notificationrulesubscribers",
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [
            PINotificationRuleSubscriber.model_validate(item) for item in items
        ]

    def update(self, web_id: str, body: dict[str, Any]) -> None:
        """Update a Notification Rule Template.

        Calls ``PATCH /notificationruletemplates/{webId}``.

        Args:
            web_id: WebID of the template to update.
            body: Partial update body with fields to change.

        Raises:
            NotFoundError: If the template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"/notificationruletemplates/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete a Notification Rule Template.

        Calls ``DELETE /notificationruletemplates/{webId}``.

        Args:
            web_id: WebID of the template to delete.

        Raises:
            NotFoundError: If no template with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/notificationruletemplates/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncNotificationRuleTemplatesMixin:
    """Async methods for AF Notification Rule Template operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> PINotificationRuleTemplate:
        """Look up an AF Notification Rule Template by its WebID.

        Calls ``GET /notificationruletemplates/{webId}``.

        Args:
            web_id: WebID of the notification rule template.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            A :class:`PINotificationRuleTemplate` populated from the API
            response.

        Raises:
            NotFoundError: If no template with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            f"/notificationruletemplates/{quote(web_id, safe='')}",
            params=params,
        )
        await raise_for_response_async(resp)
        return PINotificationRuleTemplate.model_validate(resp.json())

    async def get_by_path(
        self,
        path: str,
        *,
        selected_fields: str | None = None,
    ) -> PINotificationRuleTemplate:
        """Look up an AF Notification Rule Template by its full path.

        Args:
            path: Full AF notification rule template path.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            A :class:`PINotificationRuleTemplate` populated from the API
            response.

        Raises:
            NotFoundError: If the template path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: dict[str, Any] = {"path": path}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            "/notificationruletemplates", params=params
        )
        await raise_for_response_async(resp)
        return PINotificationRuleTemplate.model_validate(resp.json())

    async def get_by_database(
        self,
        database_web_id: str,
        *,
        name_filter: str = "*",
        max_count: int = 100,
        selected_fields: str | None = None,
    ) -> list[PINotificationRuleTemplate]:
        """List notification rule templates in an AF database.

        Args:
            database_web_id: WebID of the AF database.
            name_filter: Name pattern supporting wildcards. Defaults to
                ``"*"`` (all templates).
            max_count: Maximum number of results. Defaults to ``100``.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            List of :class:`PINotificationRuleTemplate` objects.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(database_web_id, "database_web_id")
        params: dict[str, Any] = {
            "nameFilter": name_filter,
            "maxCount": max_count,
        }
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            f"/assetdatabases/{quote(database_web_id, safe='')}"
            "/notificationruletemplates",
            params=params,
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [PINotificationRuleTemplate.model_validate(item) for item in items]

    async def create_on_database(
        self,
        database_web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Create a notification rule template on an AF database.

        Args:
            database_web_id: WebID of the parent AF database.
            body: Template definition (Name, Description, Criteria,
                ResendInterval, etc.).

        Raises:
            NotFoundError: If the database WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(database_web_id, "database_web_id")
        resp = await self._client.post(
            f"/assetdatabases/{quote(database_web_id, safe='')}"
            "/notificationruletemplates",
            json=body,
        )
        await raise_for_response_async(resp)

    async def get_subscribers(
        self,
        web_id: str,
    ) -> list[PINotificationRuleSubscriber]:
        """List subscribers for a notification rule template.

        Args:
            web_id: WebID of the notification rule template.

        Returns:
            List of :class:`PINotificationRuleSubscriber` objects.

        Raises:
            NotFoundError: If the template WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/notificationruletemplates/{quote(web_id, safe='')}"
            "/notificationrulesubscribers",
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [
            PINotificationRuleSubscriber.model_validate(item) for item in items
        ]

    async def update(self, web_id: str, body: dict[str, Any]) -> None:
        """Update a Notification Rule Template.

        Args:
            web_id: WebID of the template to update.
            body: Partial update body with fields to change.

        Raises:
            NotFoundError: If the template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"/notificationruletemplates/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete a Notification Rule Template.

        Args:
            web_id: WebID of the template to delete.

        Raises:
            NotFoundError: If no template with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/notificationruletemplates/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
