"""AF Analysis operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import Analysis

if TYPE_CHECKING:
    import httpx


class AnalysesMixin:
    """Methods for AF Analysis operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_web_id(self, web_id: str) -> Analysis:
        """Look up an AF Analysis by its WebID.

        Calls ``GET /analyses/{webId}``.

        Args:
            web_id: WebID of the analysis.

        Returns:
            An :class:`Analysis` populated from the API response.

        Raises:
            NotFoundError: If no analysis with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/analyses/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)
        return Analysis.model_validate(resp.json())

    def get_by_path(self, path: str) -> Analysis:
        """Look up an AF Analysis by its full path.

        Calls ``GET /analyses`` with a ``path`` query parameter.

        Args:
            path: Full AF analysis path, e.g.
                ``"\\\\AF_SERVER\\DB\\Element|Analysis"``.

        Returns:
            An :class:`Analysis` populated from the API response.

        Raises:
            NotFoundError: If the analysis path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/analyses", params={"path": path})
        raise_for_response(resp)
        return Analysis.model_validate(resp.json())

    def get_by_element(
        self,
        element_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[Analysis]:
        """List AF Analyses on an element.

        Calls ``GET /elements/{webId}/analyses``.

        Args:
            element_web_id: WebID of the AF element.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all analyses).
            max_count: Maximum number of results. Defaults to ``100``.

        Returns:
            List of :class:`Analysis` objects.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(element_web_id, "element_web_id")
        resp = self._client.get(
            f"/elements/{quote(element_web_id, safe='')}/analyses",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [Analysis.model_validate(item) for item in items]

    def update(
        self,
        web_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        """Update an AF Analysis's properties.

        Calls ``PATCH /analyses/{webId}``.  Only the fields that are
        provided (not ``None``) will be sent.

        Args:
            web_id: WebID of the analysis to update.
            name: New analysis name.
            description: New description.
            status: New status (e.g. ``"Enabled"``, ``"Disabled"``).
            extra_fields: Additional fields to include in the request body.

        Raises:
            NotFoundError: If no analysis with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = dict(extra_fields) if extra_fields else {}
        if name is not None:
            body["Name"] = name
        if description is not None:
            body["Description"] = description
        if status is not None:
            body["Status"] = status
        if not body:
            return
        resp = self._client.patch(
            f"/analyses/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete an AF Analysis.

        Calls ``DELETE /analyses/{webId}``.

        Args:
            web_id: WebID of the analysis to delete.

        Raises:
            NotFoundError: If no analysis with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/analyses/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncAnalysesMixin:
    """Async methods for AF Analysis operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(self, web_id: str) -> Analysis:
        """Look up an AF Analysis by its WebID.

        Calls ``GET /analyses/{webId}``.

        Args:
            web_id: WebID of the analysis.

        Returns:
            An :class:`Analysis` populated from the API response.

        Raises:
            NotFoundError: If no analysis with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/analyses/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
        return Analysis.model_validate(resp.json())

    async def get_by_path(self, path: str) -> Analysis:
        """Look up an AF Analysis by its full path.

        Calls ``GET /analyses`` with a ``path`` query parameter.

        Args:
            path: Full AF analysis path.

        Returns:
            An :class:`Analysis` populated from the API response.

        Raises:
            NotFoundError: If the analysis path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            "/analyses", params={"path": path}
        )
        await raise_for_response_async(resp)
        return Analysis.model_validate(resp.json())

    async def get_by_element(
        self,
        element_web_id: str,
        name_filter: str = "*",
        max_count: int = 100,
    ) -> list[Analysis]:
        """List AF Analyses on an element.

        Calls ``GET /elements/{webId}/analyses``.

        Args:
            element_web_id: WebID of the AF element.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all analyses).
            max_count: Maximum number of results. Defaults to ``100``.

        Returns:
            List of :class:`Analysis` objects.

        Raises:
            NotFoundError: If the element WebID is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(element_web_id, "element_web_id")
        resp = await self._client.get(
            f"/elements/{quote(element_web_id, safe='')}/analyses",
            params={"nameFilter": name_filter, "maxCount": max_count},
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", data) if isinstance(data, dict) else data
        return [Analysis.model_validate(item) for item in items]

    async def update(
        self,
        web_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        """Update an AF Analysis's properties.

        Calls ``PATCH /analyses/{webId}``.

        Args:
            web_id: WebID of the analysis to update.
            name: New analysis name.
            description: New description.
            status: New status (e.g. ``"Enabled"``, ``"Disabled"``).
            extra_fields: Additional fields to include in the request body.

        Raises:
            NotFoundError: If no analysis with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = dict(extra_fields) if extra_fields else {}
        if name is not None:
            body["Name"] = name
        if description is not None:
            body["Description"] = description
        if status is not None:
            body["Status"] = status
        if not body:
            return
        resp = await self._client.patch(
            f"/analyses/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete an AF Analysis.

        Calls ``DELETE /analyses/{webId}``.

        Args:
            web_id: WebID of the analysis to delete.

        Raises:
            NotFoundError: If no analysis with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/analyses/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
