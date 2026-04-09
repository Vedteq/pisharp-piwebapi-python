"""Time Rule operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import TimeRule

if TYPE_CHECKING:
    import httpx


class TimeRulesMixin:
    """Methods for Time Rule operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> TimeRule:
        """Look up a Time Rule by its WebID.

        Calls ``GET /timerules/{webId}``.

        Args:
            web_id: WebID of the time rule.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            A :class:`TimeRule` populated from the API response.

        Raises:
            NotFoundError: If no time rule with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            f"/timerules/{quote(web_id, safe='')}",
            params=params,
        )
        raise_for_response(resp)
        return TimeRule.model_validate(resp.json())

    def get_by_analysis(
        self,
        analysis_web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> list[TimeRule]:
        """List time rules on an analysis.

        Calls ``GET /analyses/{webId}/timerules``.

        Each analysis typically has exactly one time rule, but the API
        returns a collection for consistency.

        Args:
            analysis_web_id: WebID of the parent analysis.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            List of :class:`TimeRule` objects.

        Raises:
            NotFoundError: If the analysis WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(analysis_web_id, "analysis_web_id")
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            f"/analyses/{quote(analysis_web_id, safe='')}/timerules",
            params=params,
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [TimeRule.model_validate(item) for item in items]

    def create_on_analysis(
        self,
        analysis_web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Create a time rule on an analysis.

        Calls ``POST /analyses/{webId}/timerules``.

        Args:
            analysis_web_id: WebID of the parent analysis.
            body: Time rule definition (Name, PlugInName,
                ConfigString, etc.).

        Raises:
            NotFoundError: If the analysis WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(analysis_web_id, "analysis_web_id")
        resp = self._client.post(
            f"/analyses/{quote(analysis_web_id, safe='')}/timerules",
            json=body,
        )
        raise_for_response(resp)

    def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a Time Rule.

        Calls ``PATCH /timerules/{webId}``.

        Note: changing ``PlugInName`` (e.g. Periodic to EventTriggered)
        requires deleting and recreating the time rule.

        Args:
            web_id: WebID of the time rule.
            body: Fields to update (e.g. ``{"ConfigString": "..."}``).

        Raises:
            NotFoundError: If the time rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"/timerules/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete a Time Rule.

        Calls ``DELETE /timerules/{webId}``.

        Args:
            web_id: WebID of the time rule.

        Raises:
            NotFoundError: If the time rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/timerules/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncTimeRulesMixin:
    """Async methods for Time Rule operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> TimeRule:
        """Look up a Time Rule by its WebID.

        Calls ``GET /timerules/{webId}``.

        Args:
            web_id: WebID of the time rule.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            A :class:`TimeRule` populated from the API response.

        Raises:
            NotFoundError: If no time rule with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            f"/timerules/{quote(web_id, safe='')}",
            params=params,
        )
        await raise_for_response_async(resp)
        return TimeRule.model_validate(resp.json())

    async def get_by_analysis(
        self,
        analysis_web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> list[TimeRule]:
        """List time rules on an analysis.

        Calls ``GET /analyses/{webId}/timerules``.

        Args:
            analysis_web_id: WebID of the parent analysis.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            List of :class:`TimeRule` objects.

        Raises:
            NotFoundError: If the analysis WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(analysis_web_id, "analysis_web_id")
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            f"/analyses/{quote(analysis_web_id, safe='')}/timerules",
            params=params,
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [TimeRule.model_validate(item) for item in items]

    async def create_on_analysis(
        self,
        analysis_web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Create a time rule on an analysis.

        Calls ``POST /analyses/{webId}/timerules``.

        Args:
            analysis_web_id: WebID of the parent analysis.
            body: Time rule definition (Name, PlugInName,
                ConfigString, etc.).

        Raises:
            NotFoundError: If the analysis WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(analysis_web_id, "analysis_web_id")
        resp = await self._client.post(
            f"/analyses/{quote(analysis_web_id, safe='')}/timerules",
            json=body,
        )
        await raise_for_response_async(resp)

    async def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a Time Rule.

        Calls ``PATCH /timerules/{webId}``.

        Args:
            web_id: WebID of the time rule.
            body: Fields to update (e.g. ``{"ConfigString": "..."}``).

        Raises:
            NotFoundError: If the time rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"/timerules/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete a Time Rule.

        Calls ``DELETE /timerules/{webId}``.

        Args:
            web_id: WebID of the time rule.

        Raises:
            NotFoundError: If the time rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/timerules/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
