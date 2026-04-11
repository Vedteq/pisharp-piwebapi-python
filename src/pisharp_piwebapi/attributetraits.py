"""AF Attribute Trait operations for PI Web API.

Attribute traits are built-in role labels PI Web API uses to classify
attributes (e.g. ``LimitLoLo``, ``LimitHiHi``, ``Target``, ``Forecast``).
They are server-defined and read-only; this controller exposes only
lookup and listing endpoints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
)
from pisharp_piwebapi.models import PIAttributeTrait

if TYPE_CHECKING:
    import httpx


class AttributeTraitsMixin:
    """Methods for AF Attribute Trait operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_name(
        self,
        name: str,
        *,
        selected_fields: str | None = None,
    ) -> PIAttributeTrait:
        """Look up an Attribute Trait by its name.

        Calls ``GET /attributetraits/{name}``.

        Args:
            name: Name of the trait, e.g. ``"LimitHiHi"``.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            A :class:`PIAttributeTrait` populated from the API response.

        Raises:
            ValueError: If ``name`` is empty.
            NotFoundError: If no trait with the given name exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        if not name:
            raise ValueError("name must be a non-empty string")
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            f"/attributetraits/{quote(name, safe='')}",
            params=params,
        )
        raise_for_response(resp)
        return PIAttributeTrait.model_validate(resp.json())

    def get_multiple(
        self,
        names: list[str],
        *,
        selected_fields: str | None = None,
    ) -> list[PIAttributeTrait]:
        """Look up multiple Attribute Traits by name.

        Calls ``GET /attributetraits/multiple`` with repeated ``name``
        query parameters.

        Args:
            names: List of trait names, e.g.
                ``["LimitLoLo", "LimitHiHi", "Target"]``.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            List of :class:`PIAttributeTrait` objects, one per requested
            name. Order may not match ``names``.

        Raises:
            ValueError: If ``names`` is empty.
            NotFoundError: If the endpoint is unsupported by the server.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        if not names:
            raise ValueError("names must be a non-empty list")
        params: list[tuple[str, Any]] = [("name", n) for n in names]
        if selected_fields is not None:
            params.append(("selectedFields", selected_fields))
        resp = self._client.get("/attributetraits/multiple", params=params)
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [PIAttributeTrait.model_validate(item) for item in items]

    def get_categories(self) -> list[str]:
        """List the defined Attribute Trait categories.

        Calls ``GET /attributetraits/categories``.

        Returns:
            List of category name strings.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get("/attributetraits/categories")
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [str(item) for item in items]


class AsyncAttributeTraitsMixin:
    """Async methods for AF Attribute Trait operations."""

    _client: httpx.AsyncClient

    async def get_by_name(
        self,
        name: str,
        *,
        selected_fields: str | None = None,
    ) -> PIAttributeTrait:
        """Look up an Attribute Trait by its name.

        Calls ``GET /attributetraits/{name}``.

        Args:
            name: Name of the trait, e.g. ``"LimitHiHi"``.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            A :class:`PIAttributeTrait` populated from the API response.

        Raises:
            ValueError: If ``name`` is empty.
            NotFoundError: If no trait with the given name exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        if not name:
            raise ValueError("name must be a non-empty string")
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            f"/attributetraits/{quote(name, safe='')}",
            params=params,
        )
        await raise_for_response_async(resp)
        return PIAttributeTrait.model_validate(resp.json())

    async def get_multiple(
        self,
        names: list[str],
        *,
        selected_fields: str | None = None,
    ) -> list[PIAttributeTrait]:
        """Look up multiple Attribute Traits by name.

        Args:
            names: List of trait names.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            List of :class:`PIAttributeTrait` objects.

        Raises:
            ValueError: If ``names`` is empty.
            NotFoundError: If the endpoint is unsupported by the server.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        if not names:
            raise ValueError("names must be a non-empty list")
        params: list[tuple[str, Any]] = [("name", n) for n in names]
        if selected_fields is not None:
            params.append(("selectedFields", selected_fields))
        resp = await self._client.get(
            "/attributetraits/multiple", params=params
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [PIAttributeTrait.model_validate(item) for item in items]

    async def get_categories(self) -> list[str]:
        """List the defined Attribute Trait categories.

        Returns:
            List of category name strings.

        Raises:
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get("/attributetraits/categories")
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [str(item) for item in items]
