"""Unit Class and Unit operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PIUnit, PIUnitClass

if TYPE_CHECKING:
    import httpx


class UnitClassesMixin:
    """Methods for Unit Class and Unit operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_web_id(self, web_id: str) -> PIUnitClass:
        """Look up a Unit Class by its WebID.

        Calls ``GET /unitclasses/{webId}``.

        Args:
            web_id: WebID of the unit class.

        Returns:
            A :class:`PIUnitClass` populated from the API response.

        Raises:
            NotFoundError: If no unit class with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/unitclasses/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)
        return PIUnitClass.model_validate(resp.json())

    def get_by_path(self, path: str) -> PIUnitClass:
        """Look up a Unit Class by its full path.

        Calls ``GET /unitclasses`` with a ``path`` query parameter.

        Args:
            path: Full AF path to the unit class, e.g.
                ``"\\\\AF_SERVER\\UnitClasses[Temperature]"``.

        Returns:
            A :class:`PIUnitClass` populated from the API response.

        Raises:
            NotFoundError: If no unit class exists at the given path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            "/unitclasses", params={"path": path}
        )
        raise_for_response(resp)
        return PIUnitClass.model_validate(resp.json())

    def get_units(self, web_id: str) -> list[PIUnit]:
        """List all units within a Unit Class.

        Calls ``GET /unitclasses/{webId}/units``.

        Args:
            web_id: WebID of the unit class.

        Returns:
            A list of :class:`PIUnit` belonging to the class.

        Raises:
            NotFoundError: If no unit class with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/unitclasses/{quote(web_id, safe='')}/units"
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", data) if isinstance(data, dict) else data
        )
        return [PIUnit.model_validate(item) for item in items]

    def get_canonical_unit(self, web_id: str) -> PIUnit:
        """Get the canonical (base) unit for a Unit Class.

        Calls ``GET /unitclasses/{webId}/canonicalunit``.

        Args:
            web_id: WebID of the unit class.

        Returns:
            The canonical :class:`PIUnit` for the class.

        Raises:
            NotFoundError: If no unit class with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/unitclasses/{quote(web_id, safe='')}/canonicalunit"
        )
        raise_for_response(resp)
        return PIUnit.model_validate(resp.json())

    def create_unit(
        self,
        web_id: str,
        name: str,
        abbreviation: str,
        *,
        factor: float = 1.0,
        offset: float = 0.0,
        description: str = "",
        reference_factor: float = 0.0,
        reference_offset: float = 0.0,
        reference_unit_abbreviation: str = "",
    ) -> None:
        """Create a new unit within a Unit Class.

        Calls ``POST /unitclasses/{webId}/units``.

        Args:
            web_id: WebID of the unit class.
            name: Display name of the new unit.
            abbreviation: Short abbreviation (e.g. ``"degF"``).
            factor: Conversion factor to canonical unit.
            offset: Conversion offset to canonical unit.
            description: Optional description.
            reference_factor: Reference conversion factor.
            reference_offset: Reference conversion offset.
            reference_unit_abbreviation: Abbreviation of reference unit.

        Raises:
            NotFoundError: If the unit class WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = {
            "Name": name,
            "Abbreviation": abbreviation,
            "Factor": factor,
            "Offset": offset,
        }
        if description:
            body["Description"] = description
        if reference_factor:
            body["ReferenceFactor"] = reference_factor
        if reference_offset:
            body["ReferenceOffset"] = reference_offset
        if reference_unit_abbreviation:
            body["ReferenceUnitAbbreviation"] = reference_unit_abbreviation
        resp = self._client.post(
            f"/unitclasses/{quote(web_id, safe='')}/units",
            json=body,
        )
        raise_for_response(resp)

    def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a Unit Class.

        Calls ``PATCH /unitclasses/{webId}``.

        Args:
            web_id: WebID of the unit class.
            body: Fields to update (e.g. ``{"Description": "new desc"}``).

        Raises:
            NotFoundError: If the unit class WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"/unitclasses/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete a Unit Class.

        Calls ``DELETE /unitclasses/{webId}``.

        Args:
            web_id: WebID of the unit class.

        Raises:
            NotFoundError: If the unit class WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/unitclasses/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)

    def get_unit_by_web_id(self, web_id: str) -> PIUnit:
        """Look up a Unit by its WebID.

        Calls ``GET /units/{webId}``.

        Args:
            web_id: WebID of the unit.

        Returns:
            A :class:`PIUnit` populated from the API response.

        Raises:
            NotFoundError: If no unit with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/units/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)
        return PIUnit.model_validate(resp.json())

    def update_unit(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a Unit.

        Calls ``PATCH /units/{webId}``.

        Args:
            web_id: WebID of the unit.
            body: Fields to update (e.g. ``{"Description": "new desc"}``).

        Raises:
            NotFoundError: If the unit WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"/units/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete_unit(self, web_id: str) -> None:
        """Delete a Unit.

        Calls ``DELETE /units/{webId}``.

        Args:
            web_id: WebID of the unit.

        Raises:
            NotFoundError: If the unit WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/units/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncUnitClassesMixin:
    """Async methods for Unit Class and Unit operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(self, web_id: str) -> PIUnitClass:
        """Look up a Unit Class by its WebID.

        Calls ``GET /unitclasses/{webId}``.

        Args:
            web_id: WebID of the unit class.

        Returns:
            A :class:`PIUnitClass` populated from the API response.

        Raises:
            NotFoundError: If no unit class with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/unitclasses/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
        return PIUnitClass.model_validate(resp.json())

    async def get_by_path(self, path: str) -> PIUnitClass:
        """Look up a Unit Class by its full path.

        Calls ``GET /unitclasses`` with a ``path`` query parameter.

        Args:
            path: Full AF path to the unit class.

        Returns:
            A :class:`PIUnitClass` populated from the API response.

        Raises:
            NotFoundError: If no unit class exists at the given path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            "/unitclasses", params={"path": path}
        )
        await raise_for_response_async(resp)
        return PIUnitClass.model_validate(resp.json())

    async def get_units(self, web_id: str) -> list[PIUnit]:
        """List all units within a Unit Class.

        Calls ``GET /unitclasses/{webId}/units``.

        Args:
            web_id: WebID of the unit class.

        Returns:
            A list of :class:`PIUnit` belonging to the class.

        Raises:
            NotFoundError: If no unit class with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/unitclasses/{quote(web_id, safe='')}/units"
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", data) if isinstance(data, dict) else data
        )
        return [PIUnit.model_validate(item) for item in items]

    async def get_canonical_unit(self, web_id: str) -> PIUnit:
        """Get the canonical (base) unit for a Unit Class.

        Calls ``GET /unitclasses/{webId}/canonicalunit``.

        Args:
            web_id: WebID of the unit class.

        Returns:
            The canonical :class:`PIUnit` for the class.

        Raises:
            NotFoundError: If no unit class with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/unitclasses/{quote(web_id, safe='')}/canonicalunit"
        )
        await raise_for_response_async(resp)
        return PIUnit.model_validate(resp.json())

    async def create_unit(
        self,
        web_id: str,
        name: str,
        abbreviation: str,
        *,
        factor: float = 1.0,
        offset: float = 0.0,
        description: str = "",
        reference_factor: float = 0.0,
        reference_offset: float = 0.0,
        reference_unit_abbreviation: str = "",
    ) -> None:
        """Create a new unit within a Unit Class.

        Calls ``POST /unitclasses/{webId}/units``.

        Args:
            web_id: WebID of the unit class.
            name: Display name of the new unit.
            abbreviation: Short abbreviation (e.g. ``"degF"``).
            factor: Conversion factor to canonical unit.
            offset: Conversion offset to canonical unit.
            description: Optional description.
            reference_factor: Reference conversion factor.
            reference_offset: Reference conversion offset.
            reference_unit_abbreviation: Abbreviation of reference unit.

        Raises:
            NotFoundError: If the unit class WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        body: dict[str, Any] = {
            "Name": name,
            "Abbreviation": abbreviation,
            "Factor": factor,
            "Offset": offset,
        }
        if description:
            body["Description"] = description
        if reference_factor:
            body["ReferenceFactor"] = reference_factor
        if reference_offset:
            body["ReferenceOffset"] = reference_offset
        if reference_unit_abbreviation:
            body["ReferenceUnitAbbreviation"] = reference_unit_abbreviation
        resp = await self._client.post(
            f"/unitclasses/{quote(web_id, safe='')}/units",
            json=body,
        )
        await raise_for_response_async(resp)

    async def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a Unit Class.

        Calls ``PATCH /unitclasses/{webId}``.

        Args:
            web_id: WebID of the unit class.
            body: Fields to update (e.g. ``{"Description": "new desc"}``).

        Raises:
            NotFoundError: If the unit class WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"/unitclasses/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete a Unit Class.

        Calls ``DELETE /unitclasses/{webId}``.

        Args:
            web_id: WebID of the unit class.

        Raises:
            NotFoundError: If the unit class WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/unitclasses/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)

    async def get_unit_by_web_id(self, web_id: str) -> PIUnit:
        """Look up a Unit by its WebID.

        Calls ``GET /units/{webId}``.

        Args:
            web_id: WebID of the unit.

        Returns:
            A :class:`PIUnit` populated from the API response.

        Raises:
            NotFoundError: If no unit with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/units/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
        return PIUnit.model_validate(resp.json())

    async def update_unit(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a Unit.

        Calls ``PATCH /units/{webId}``.

        Args:
            web_id: WebID of the unit.
            body: Fields to update (e.g. ``{"Description": "new desc"}``).

        Raises:
            NotFoundError: If the unit WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"/units/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete_unit(self, web_id: str) -> None:
        """Delete a Unit.

        Calls ``DELETE /units/{webId}``.

        Args:
            web_id: WebID of the unit.

        Raises:
            NotFoundError: If the unit WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/units/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
