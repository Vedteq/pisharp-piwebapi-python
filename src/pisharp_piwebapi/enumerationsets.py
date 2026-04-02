"""Enumeration Set operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import EnumerationSet, EnumerationValue

if TYPE_CHECKING:
    import httpx


class EnumerationSetsMixin:
    """Methods for Enumeration Set operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_web_id(self, web_id: str) -> EnumerationSet:
        """Look up an Enumeration Set by its WebID.

        Calls ``GET /enumerationsets/{webId}``.

        Args:
            web_id: WebID of the enumeration set.

        Returns:
            An :class:`EnumerationSet` populated from the API response.

        Raises:
            NotFoundError: If no enumeration set with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/enumerationsets/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)
        return EnumerationSet.model_validate(resp.json())

    def get_by_path(self, path: str) -> EnumerationSet:
        """Look up an Enumeration Set by its full path.

        Calls ``GET /enumerationsets`` with a ``path`` query parameter.

        Args:
            path: Full AF path to the enumeration set, e.g.
                ``"\\\\AF_SERVER\\DATABASE\\EnumerationSets[SetName]"``.

        Returns:
            An :class:`EnumerationSet` populated from the API response.

        Raises:
            NotFoundError: If no enumeration set exists at the given path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            "/enumerationsets", params={"path": path}
        )
        raise_for_response(resp)
        return EnumerationSet.model_validate(resp.json())

    def get_values(
        self,
        web_id: str,
    ) -> list[EnumerationValue]:
        """List all values (members) of an Enumeration Set.

        Calls ``GET /enumerationsets/{webId}/enumerationvalues``.

        Args:
            web_id: WebID of the enumeration set.

        Returns:
            A list of :class:`EnumerationValue` items in the set.

        Raises:
            NotFoundError: If no enumeration set with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/enumerationsets/{quote(web_id, safe='')}/enumerationvalues"
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = data.get("Items", data) if isinstance(data, dict) else data
        return [EnumerationValue.model_validate(item) for item in items]

    def get_by_data_server(
        self,
        data_server_web_id: str,
    ) -> list[EnumerationSet]:
        """List all Enumeration Sets on a Data Server.

        Calls ``GET /dataservers/{webId}/enumerationsets``.

        Args:
            data_server_web_id: WebID of the PI Data Server.

        Returns:
            A list of :class:`EnumerationSet` on the server.

        Raises:
            NotFoundError: If the data server WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(data_server_web_id, "data_server_web_id")
        resp = self._client.get(
            f"/dataservers/{quote(data_server_web_id, safe='')}/enumerationsets"
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = data.get("Items", data) if isinstance(data, dict) else data
        return [EnumerationSet.model_validate(item) for item in items]

    def create_value(
        self,
        web_id: str,
        name: str,
        value: int,
        *,
        description: str = "",
    ) -> None:
        """Create a new value in an Enumeration Set.

        Calls ``POST /enumerationsets/{webId}/enumerationvalues``.

        Args:
            web_id: WebID of the enumeration set.
            name: Display name of the new enumeration value.
            value: Integer value (ordinal) for the enumeration member.
            description: Optional description.

        Raises:
            NotFoundError: If the enumeration set WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = {"Name": name, "Value": value}
        if description:
            body["Description"] = description
        resp = self._client.post(
            f"/enumerationsets/{quote(web_id, safe='')}/enumerationvalues",
            json=body,
        )
        raise_for_response(resp)


class AsyncEnumerationSetsMixin:
    """Async methods for Enumeration Set operations. Mixed into the async client."""

    _client: httpx.AsyncClient

    async def get_by_web_id(self, web_id: str) -> EnumerationSet:
        """Look up an Enumeration Set by its WebID.

        Calls ``GET /enumerationsets/{webId}``.

        Args:
            web_id: WebID of the enumeration set.

        Returns:
            An :class:`EnumerationSet` populated from the API response.

        Raises:
            NotFoundError: If no enumeration set with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/enumerationsets/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
        return EnumerationSet.model_validate(resp.json())

    async def get_by_path(self, path: str) -> EnumerationSet:
        """Look up an Enumeration Set by its full path.

        Calls ``GET /enumerationsets`` with a ``path`` query parameter.

        Args:
            path: Full AF path to the enumeration set.

        Returns:
            An :class:`EnumerationSet` populated from the API response.

        Raises:
            NotFoundError: If no enumeration set exists at the given path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            "/enumerationsets", params={"path": path}
        )
        await raise_for_response_async(resp)
        return EnumerationSet.model_validate(resp.json())

    async def get_values(
        self,
        web_id: str,
    ) -> list[EnumerationValue]:
        """List all values (members) of an Enumeration Set.

        Calls ``GET /enumerationsets/{webId}/enumerationvalues``.

        Args:
            web_id: WebID of the enumeration set.

        Returns:
            A list of :class:`EnumerationValue` items in the set.

        Raises:
            NotFoundError: If no enumeration set with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/enumerationsets/{quote(web_id, safe='')}/enumerationvalues"
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", data) if isinstance(data, dict) else data
        )
        return [EnumerationValue.model_validate(item) for item in items]

    async def get_by_data_server(
        self,
        data_server_web_id: str,
    ) -> list[EnumerationSet]:
        """List all Enumeration Sets on a Data Server.

        Calls ``GET /dataservers/{webId}/enumerationsets``.

        Args:
            data_server_web_id: WebID of the PI Data Server.

        Returns:
            A list of :class:`EnumerationSet` on the server.

        Raises:
            NotFoundError: If the data server WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(data_server_web_id, "data_server_web_id")
        resp = await self._client.get(
            f"/dataservers/{quote(data_server_web_id, safe='')}/enumerationsets"
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", data) if isinstance(data, dict) else data
        )
        return [EnumerationSet.model_validate(item) for item in items]

    async def create_value(
        self,
        web_id: str,
        name: str,
        value: int,
        *,
        description: str = "",
    ) -> None:
        """Create a new value in an Enumeration Set.

        Calls ``POST /enumerationsets/{webId}/enumerationvalues``.

        Args:
            web_id: WebID of the enumeration set.
            name: Display name of the new enumeration value.
            value: Integer value (ordinal) for the enumeration member.
            description: Optional description.

        Raises:
            NotFoundError: If the enumeration set WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = {"Name": name, "Value": value}
        if description:
            body["Description"] = description
        resp = await self._client.post(
            f"/enumerationsets/{quote(web_id, safe='')}/enumerationvalues",
            json=body,
        )
        await raise_for_response_async(resp)
