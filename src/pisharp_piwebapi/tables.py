"""AF Table operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PITable, PITableData

if TYPE_CHECKING:
    import httpx


class TablesMixin:
    """Methods for AF Table operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_web_id(self, web_id: str) -> PITable:
        """Look up an AF Table by its WebID.

        Calls ``GET /tables/{webId}``.

        Args:
            web_id: WebID of the table.

        Returns:
            A :class:`PITable` populated from the API response.

        Raises:
            NotFoundError: If no table with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/tables/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)
        return PITable.model_validate(resp.json())

    def get_by_path(self, path: str) -> PITable:
        """Look up an AF Table by its full path.

        Calls ``GET /tables`` with a ``path`` query parameter.

        Args:
            path: Full AF table path, e.g.
                ``"\\\\AF_SERVER\\DB\\Tables[LookupTable]"``.

        Returns:
            A :class:`PITable` populated from the API response.

        Raises:
            NotFoundError: If the table path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/tables", params={"path": path})
        raise_for_response(resp)
        return PITable.model_validate(resp.json())

    def get_data(self, web_id: str) -> PITableData:
        """Retrieve row data from an AF Table.

        Calls ``GET /tables/{webId}/data``.

        Args:
            web_id: WebID of the table.

        Returns:
            A :class:`PITableData` containing columns and rows.

        Raises:
            NotFoundError: If no table with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/tables/{quote(web_id, safe='')}/data"
        )
        raise_for_response(resp)
        return PITableData.model_validate(resp.json())

    def update_data(
        self,
        web_id: str,
        data: dict[str, Any],
    ) -> None:
        """Replace the row data in an AF Table.

        Calls ``PUT /tables/{webId}/data``.

        Args:
            web_id: WebID of the table.
            data: Table data dict with ``"Columns"`` and ``"Rows"``
                keys matching the PI Web API schema.

        Raises:
            NotFoundError: If no table with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.put(
            f"/tables/{quote(web_id, safe='')}/data",
            json=data,
        )
        raise_for_response(resp)

    def update(
        self,
        web_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        """Update an AF Table's properties.

        Calls ``PATCH /tables/{webId}``.  Only the fields that are
        provided (not ``None``) will be sent.

        Args:
            web_id: WebID of the table to update.
            name: New table name.
            description: New description.
            extra_fields: Additional fields to include in the request body.

        Raises:
            NotFoundError: If no table with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = dict(extra_fields) if extra_fields else {}
        if name is not None:
            body["Name"] = name
        if description is not None:
            body["Description"] = description
        if not body:
            return
        resp = self._client.patch(
            f"/tables/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete an AF Table.

        Calls ``DELETE /tables/{webId}``.

        Args:
            web_id: WebID of the table to delete.

        Raises:
            NotFoundError: If no table with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/tables/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncTablesMixin:
    """Async methods for AF Table operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(self, web_id: str) -> PITable:
        """Look up an AF Table by its WebID.

        Calls ``GET /tables/{webId}``.

        Args:
            web_id: WebID of the table.

        Returns:
            A :class:`PITable` populated from the API response.

        Raises:
            NotFoundError: If no table with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/tables/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
        return PITable.model_validate(resp.json())

    async def get_by_path(self, path: str) -> PITable:
        """Look up an AF Table by its full path.

        Calls ``GET /tables`` with a ``path`` query parameter.

        Args:
            path: Full AF table path.

        Returns:
            A :class:`PITable` populated from the API response.

        Raises:
            NotFoundError: If the table path is not found.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            "/tables", params={"path": path}
        )
        await raise_for_response_async(resp)
        return PITable.model_validate(resp.json())

    async def get_data(self, web_id: str) -> PITableData:
        """Retrieve row data from an AF Table.

        Calls ``GET /tables/{webId}/data``.

        Args:
            web_id: WebID of the table.

        Returns:
            A :class:`PITableData` containing columns and rows.

        Raises:
            NotFoundError: If no table with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/tables/{quote(web_id, safe='')}/data"
        )
        await raise_for_response_async(resp)
        return PITableData.model_validate(resp.json())

    async def update_data(
        self,
        web_id: str,
        data: dict[str, Any],
    ) -> None:
        """Replace the row data in an AF Table.

        Calls ``PUT /tables/{webId}/data``.

        Args:
            web_id: WebID of the table.
            data: Table data dict with ``"Columns"`` and ``"Rows"``
                keys matching the PI Web API schema.

        Raises:
            NotFoundError: If no table with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.put(
            f"/tables/{quote(web_id, safe='')}/data",
            json=data,
        )
        await raise_for_response_async(resp)

    async def update(
        self,
        web_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        """Update an AF Table's properties.

        Calls ``PATCH /tables/{webId}``.

        Args:
            web_id: WebID of the table to update.
            name: New table name.
            description: New description.
            extra_fields: Additional fields to include in the request body.

        Raises:
            NotFoundError: If no table with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = dict(extra_fields) if extra_fields else {}
        if name is not None:
            body["Name"] = name
        if description is not None:
            body["Description"] = description
        if not body:
            return
        resp = await self._client.patch(
            f"/tables/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete an AF Table.

        Calls ``DELETE /tables/{webId}``.

        Args:
            web_id: WebID of the table to delete.

        Raises:
            NotFoundError: If no table with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/tables/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
