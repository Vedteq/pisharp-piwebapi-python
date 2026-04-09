"""Enumeration Value standalone operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import EnumerationValue

if TYPE_CHECKING:
    import httpx


class EnumerationValuesMixin:
    """Methods for standalone Enumeration Value operations.

    Mixed into the sync client. For listing and creating values within
    an enumeration set, see ``EnumerationSetsMixin``.
    """

    _client: httpx.Client

    def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> EnumerationValue:
        """Look up an Enumeration Value by its WebID.

        Calls ``GET /enumerationvalues/{webId}``.

        Args:
            web_id: WebID of the enumeration value.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            An :class:`EnumerationValue` populated from the API response.

        Raises:
            NotFoundError: If no enumeration value with the given
                WebID exists.
            AuthenticationError: If the request is rejected as
                unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            f"/enumerationvalues/{quote(web_id, safe='')}",
            params=params,
        )
        raise_for_response(resp)
        return EnumerationValue.model_validate(resp.json())

    def get_by_path(
        self,
        path: str,
        *,
        selected_fields: str | None = None,
    ) -> EnumerationValue:
        """Look up an Enumeration Value by its full path.

        Calls ``GET /enumerationvalues`` with a ``path`` query parameter.

        Args:
            path: Full AF path to the enumeration value, e.g.
                ``"\\\\AF_SERVER\\DB\\EnumSets[Status]\\Running"``.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            An :class:`EnumerationValue` populated from the API response.

        Raises:
            NotFoundError: If no enumeration value exists at the path.
            AuthenticationError: If the request is rejected as
                unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: dict[str, Any] = {"path": path}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            "/enumerationvalues",
            params=params,
        )
        raise_for_response(resp)
        return EnumerationValue.model_validate(resp.json())

    def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an Enumeration Value.

        Calls ``PATCH /enumerationvalues/{webId}``.

        Args:
            web_id: WebID of the enumeration value.
            body: Fields to update (e.g.
                ``{"Description": "new desc"}``).

        Raises:
            NotFoundError: If the enumeration value WebID is invalid.
            AuthenticationError: If the request is rejected as
                unauthorized.
            PIWebAPIError: For any other non-2xx response. System
                enumeration sets are read-only and will return 403.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"/enumerationvalues/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete an Enumeration Value.

        Calls ``DELETE /enumerationvalues/{webId}``.

        Note: deleting a value that is referenced by archived data does
        not remove historical records. The Data Archive stores the
        integer ordinal; deleted values appear as
        ``"No Digital State [n]"`` in clients.

        Args:
            web_id: WebID of the enumeration value.

        Raises:
            NotFoundError: If the enumeration value WebID is invalid.
            AuthenticationError: If the request is rejected as
                unauthorized.
            PIWebAPIError: For any other non-2xx response. System
                enumeration sets are read-only and will return 403.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/enumerationvalues/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncEnumerationValuesMixin:
    """Async methods for standalone Enumeration Value operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> EnumerationValue:
        """Look up an Enumeration Value by its WebID.

        Calls ``GET /enumerationvalues/{webId}``.

        Args:
            web_id: WebID of the enumeration value.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            An :class:`EnumerationValue` populated from the API response.

        Raises:
            NotFoundError: If no enumeration value with the given
                WebID exists.
            AuthenticationError: If the request is rejected as
                unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            f"/enumerationvalues/{quote(web_id, safe='')}",
            params=params,
        )
        await raise_for_response_async(resp)
        return EnumerationValue.model_validate(resp.json())

    async def get_by_path(
        self,
        path: str,
        *,
        selected_fields: str | None = None,
    ) -> EnumerationValue:
        """Look up an Enumeration Value by its full path.

        Calls ``GET /enumerationvalues`` with a ``path`` query parameter.

        Args:
            path: Full AF path to the enumeration value.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            An :class:`EnumerationValue` populated from the API response.

        Raises:
            NotFoundError: If no enumeration value exists at the path.
            AuthenticationError: If the request is rejected as
                unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        params: dict[str, Any] = {"path": path}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            "/enumerationvalues",
            params=params,
        )
        await raise_for_response_async(resp)
        return EnumerationValue.model_validate(resp.json())

    async def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an Enumeration Value.

        Calls ``PATCH /enumerationvalues/{webId}``.

        Args:
            web_id: WebID of the enumeration value.
            body: Fields to update (e.g.
                ``{"Description": "new desc"}``).

        Raises:
            NotFoundError: If the enumeration value WebID is invalid.
            AuthenticationError: If the request is rejected as
                unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"/enumerationvalues/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete an Enumeration Value.

        Calls ``DELETE /enumerationvalues/{webId}``.

        Args:
            web_id: WebID of the enumeration value.

        Raises:
            NotFoundError: If the enumeration value WebID is invalid.
            AuthenticationError: If the request is rejected as
                unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/enumerationvalues/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
