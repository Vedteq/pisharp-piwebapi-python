"""AF Element Template operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PIAttributeTemplate, PIElementTemplate

if TYPE_CHECKING:
    import httpx


class ElementTemplatesMixin:
    """Methods for AF Element Template operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_web_id(self, web_id: str) -> PIElementTemplate:
        """Look up an AF Element Template by its WebID.

        Calls ``GET /elementtemplates/{webId}``.

        Args:
            web_id: WebID of the element template.

        Returns:
            A :class:`PIElementTemplate` populated from the API response.

        Raises:
            NotFoundError: If no template with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/elementtemplates/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)
        return PIElementTemplate.model_validate(resp.json())

    def get_by_path(self, path: str) -> PIElementTemplate:
        """Look up an AF Element Template by its full path.

        The path follows the AF hierarchy, e.g.
        ``"\\\\AF_SERVER\\DATABASE\\ElementTemplates[TemplateName]"``.

        Calls ``GET /elementtemplates`` with a ``path`` query parameter.

        Args:
            path: Full AF element template path.

        Returns:
            A :class:`PIElementTemplate` populated from the API response.

        Raises:
            NotFoundError: If the template path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            "/elementtemplates", params={"path": path}
        )
        raise_for_response(resp)
        return PIElementTemplate.model_validate(resp.json())

    def get_by_database(
        self,
        database_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIElementTemplate]:
        """List AF Element Templates in a database.

        Calls ``GET /assetdatabases/{webId}/elementtemplates``.

        Args:
            database_web_id: WebID of the AF database.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all templates).
            max_count: Maximum number of results to return.
                Defaults to ``100``.

        Returns:
            List of :class:`PIElementTemplate` objects.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(database_web_id, "database_web_id")
        resp = self._client.get(
            f"/assetdatabases/{quote(database_web_id, safe='')}"
            "/elementtemplates",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIElementTemplate.model_validate(item) for item in items]

    def get_attribute_templates(
        self,
        template_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIAttributeTemplate]:
        """List attribute templates defined on an element template.

        Calls ``GET /elementtemplates/{webId}/attributetemplates``.

        Args:
            template_web_id: WebID of the element template.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all attribute templates).
            max_count: Maximum number of results to return.
                Defaults to ``100``.

        Returns:
            List of :class:`PIAttributeTemplate` objects.

        Raises:
            NotFoundError: If the template WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(template_web_id, "template_web_id")
        resp = self._client.get(
            f"/elementtemplates/{quote(template_web_id, safe='')}"
            "/attributetemplates",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIAttributeTemplate.model_validate(item) for item in items]


class AsyncElementTemplatesMixin:
    """Async methods for AF Element Template operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(self, web_id: str) -> PIElementTemplate:
        """Look up an AF Element Template by its WebID.

        Calls ``GET /elementtemplates/{webId}``.

        Args:
            web_id: WebID of the element template.

        Returns:
            A :class:`PIElementTemplate` populated from the API response.

        Raises:
            NotFoundError: If no template with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/elementtemplates/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
        return PIElementTemplate.model_validate(resp.json())

    async def get_by_path(self, path: str) -> PIElementTemplate:
        """Look up an AF Element Template by its full path.

        Calls ``GET /elementtemplates`` with a ``path`` query parameter.

        Args:
            path: Full AF element template path.

        Returns:
            A :class:`PIElementTemplate` populated from the API response.

        Raises:
            NotFoundError: If the template path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            "/elementtemplates", params={"path": path}
        )
        await raise_for_response_async(resp)
        return PIElementTemplate.model_validate(resp.json())

    async def get_by_database(
        self,
        database_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIElementTemplate]:
        """List AF Element Templates in a database.

        Calls ``GET /assetdatabases/{webId}/elementtemplates``.

        Args:
            database_web_id: WebID of the AF database.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all templates).
            max_count: Maximum number of results to return.
                Defaults to ``100``.

        Returns:
            List of :class:`PIElementTemplate` objects.

        Raises:
            NotFoundError: If the database WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(database_web_id, "database_web_id")
        resp = await self._client.get(
            f"/assetdatabases/{quote(database_web_id, safe='')}"
            "/elementtemplates",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIElementTemplate.model_validate(item) for item in items]

    async def get_attribute_templates(
        self,
        template_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[PIAttributeTemplate]:
        """List attribute templates defined on an element template.

        Calls ``GET /elementtemplates/{webId}/attributetemplates``.

        Args:
            template_web_id: WebID of the element template.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all attribute templates).
            max_count: Maximum number of results to return.
                Defaults to ``100``.

        Returns:
            List of :class:`PIAttributeTemplate` objects.

        Raises:
            NotFoundError: If the template WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(template_web_id, "template_web_id")
        resp = await self._client.get(
            f"/elementtemplates/{quote(template_web_id, safe='')}"
            "/attributetemplates",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [PIAttributeTemplate.model_validate(item) for item in items]
