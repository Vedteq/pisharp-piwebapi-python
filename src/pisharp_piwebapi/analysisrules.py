"""Analysis Rule operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PIAnalysisRule

if TYPE_CHECKING:
    import httpx


class AnalysisRulesMixin:
    """Methods for Analysis Rule operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> PIAnalysisRule:
        """Look up an Analysis Rule by its WebID.

        Calls ``GET /analysisrules/{webId}``.

        Args:
            web_id: WebID of the analysis rule.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            A :class:`PIAnalysisRule` populated from the API response.

        Raises:
            NotFoundError: If no analysis rule with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            f"/analysisrules/{quote(web_id, safe='')}",
            params=params,
        )
        raise_for_response(resp)
        return PIAnalysisRule.model_validate(resp.json())

    def get_children(
        self,
        web_id: str,
        *,
        name_filter: str = "*",
        max_count: int = 100,
        selected_fields: str | None = None,
    ) -> list[PIAnalysisRule]:
        """List child analysis rules of an analysis rule.

        Calls ``GET /analysisrules/{webId}/analysisrules``.

        Args:
            web_id: WebID of the parent analysis rule.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all).
            max_count: Maximum number of results. Defaults to ``100``.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            List of :class:`PIAnalysisRule` objects.

        Raises:
            NotFoundError: If the parent analysis rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {
            "nameFilter": name_filter,
            "maxCount": max_count,
        }
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            f"/analysisrules/{quote(web_id, safe='')}/analysisrules",
            params=params,
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [PIAnalysisRule.model_validate(item) for item in items]

    def create_child(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Create a child analysis rule under an existing analysis rule.

        Calls ``POST /analysisrules/{webId}/analysisrules``.

        Args:
            web_id: WebID of the parent analysis rule.
            body: Analysis rule definition (Name, PlugInName,
                ConfigString, VariableMapping, etc.).

        Raises:
            NotFoundError: If the parent analysis rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.post(
            f"/analysisrules/{quote(web_id, safe='')}/analysisrules",
            json=body,
        )
        raise_for_response(resp)

    def get_by_analysis(
        self,
        analysis_web_id: str,
        *,
        name_filter: str = "*",
        max_count: int = 100,
        selected_fields: str | None = None,
    ) -> list[PIAnalysisRule]:
        """List root analysis rules on an analysis.

        Calls ``GET /analyses/{webId}/analysisrules``.

        Args:
            analysis_web_id: WebID of the parent analysis.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all).
            max_count: Maximum number of results. Defaults to ``100``.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            List of :class:`PIAnalysisRule` objects.

        Raises:
            NotFoundError: If the analysis WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(analysis_web_id, "analysis_web_id")
        params: dict[str, Any] = {
            "nameFilter": name_filter,
            "maxCount": max_count,
        }
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = self._client.get(
            f"/analyses/{quote(analysis_web_id, safe='')}/analysisrules",
            params=params,
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [PIAnalysisRule.model_validate(item) for item in items]

    def create_on_analysis(
        self,
        analysis_web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Create a root analysis rule on an analysis.

        Calls ``POST /analyses/{webId}/analysisrules``.

        Args:
            analysis_web_id: WebID of the parent analysis.
            body: Analysis rule definition (Name, PlugInName,
                ConfigString, VariableMapping, etc.).

        Raises:
            NotFoundError: If the analysis WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(analysis_web_id, "analysis_web_id")
        resp = self._client.post(
            f"/analyses/{quote(analysis_web_id, safe='')}/analysisrules",
            json=body,
        )
        raise_for_response(resp)

    def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an Analysis Rule.

        Calls ``PATCH /analysisrules/{webId}``.

        Args:
            web_id: WebID of the analysis rule.
            body: Fields to update (e.g. ``{"ConfigString": "..."}``).

        Raises:
            NotFoundError: If the analysis rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"/analysisrules/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete an Analysis Rule.

        Calls ``DELETE /analysisrules/{webId}``.

        Args:
            web_id: WebID of the analysis rule.

        Raises:
            NotFoundError: If the analysis rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/analysisrules/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncAnalysisRulesMixin:
    """Async methods for Analysis Rule operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(
        self,
        web_id: str,
        *,
        selected_fields: str | None = None,
    ) -> PIAnalysisRule:
        """Look up an Analysis Rule by its WebID.

        Calls ``GET /analysisrules/{webId}``.

        Args:
            web_id: WebID of the analysis rule.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            A :class:`PIAnalysisRule` populated from the API response.

        Raises:
            NotFoundError: If no analysis rule with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {}
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            f"/analysisrules/{quote(web_id, safe='')}",
            params=params,
        )
        await raise_for_response_async(resp)
        return PIAnalysisRule.model_validate(resp.json())

    async def get_children(
        self,
        web_id: str,
        *,
        name_filter: str = "*",
        max_count: int = 100,
        selected_fields: str | None = None,
    ) -> list[PIAnalysisRule]:
        """List child analysis rules of an analysis rule.

        Calls ``GET /analysisrules/{webId}/analysisrules``.

        Args:
            web_id: WebID of the parent analysis rule.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all).
            max_count: Maximum number of results. Defaults to ``100``.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            List of :class:`PIAnalysisRule` objects.

        Raises:
            NotFoundError: If the parent analysis rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        params: dict[str, Any] = {
            "nameFilter": name_filter,
            "maxCount": max_count,
        }
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            f"/analysisrules/{quote(web_id, safe='')}/analysisrules",
            params=params,
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [PIAnalysisRule.model_validate(item) for item in items]

    async def create_child(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Create a child analysis rule under an existing analysis rule.

        Calls ``POST /analysisrules/{webId}/analysisrules``.

        Args:
            web_id: WebID of the parent analysis rule.
            body: Analysis rule definition (Name, PlugInName,
                ConfigString, VariableMapping, etc.).

        Raises:
            NotFoundError: If the parent analysis rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.post(
            f"/analysisrules/{quote(web_id, safe='')}/analysisrules",
            json=body,
        )
        await raise_for_response_async(resp)

    async def get_by_analysis(
        self,
        analysis_web_id: str,
        *,
        name_filter: str = "*",
        max_count: int = 100,
        selected_fields: str | None = None,
    ) -> list[PIAnalysisRule]:
        """List root analysis rules on an analysis.

        Calls ``GET /analyses/{webId}/analysisrules``.

        Args:
            analysis_web_id: WebID of the parent analysis.
            name_filter: Name pattern supporting wildcards.
                Defaults to ``"*"`` (all).
            max_count: Maximum number of results. Defaults to ``100``.
            selected_fields: Comma-separated list of fields to return.

        Returns:
            List of :class:`PIAnalysisRule` objects.

        Raises:
            NotFoundError: If the analysis WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(analysis_web_id, "analysis_web_id")
        params: dict[str, Any] = {
            "nameFilter": name_filter,
            "maxCount": max_count,
        }
        if selected_fields is not None:
            params["selectedFields"] = selected_fields
        resp = await self._client.get(
            f"/analyses/{quote(analysis_web_id, safe='')}/analysisrules",
            params=params,
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [PIAnalysisRule.model_validate(item) for item in items]

    async def create_on_analysis(
        self,
        analysis_web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Create a root analysis rule on an analysis.

        Calls ``POST /analyses/{webId}/analysisrules``.

        Args:
            analysis_web_id: WebID of the parent analysis.
            body: Analysis rule definition (Name, PlugInName,
                ConfigString, VariableMapping, etc.).

        Raises:
            NotFoundError: If the analysis WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(analysis_web_id, "analysis_web_id")
        resp = await self._client.post(
            f"/analyses/{quote(analysis_web_id, safe='')}/analysisrules",
            json=body,
        )
        await raise_for_response_async(resp)

    async def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an Analysis Rule.

        Calls ``PATCH /analysisrules/{webId}``.

        Args:
            web_id: WebID of the analysis rule.
            body: Fields to update (e.g. ``{"ConfigString": "..."}``).

        Raises:
            NotFoundError: If the analysis rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"/analysisrules/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete an Analysis Rule.

        Calls ``DELETE /analysisrules/{webId}``.

        Args:
            web_id: WebID of the analysis rule.

        Raises:
            NotFoundError: If the analysis rule WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/analysisrules/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
