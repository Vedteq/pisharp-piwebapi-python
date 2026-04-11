"""Analysis Template operations for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PIAnalysisTemplate

if TYPE_CHECKING:
    import httpx


class AnalysisTemplatesMixin:
    """Methods for Analysis Template operations. Mixed into the sync client."""

    _client: httpx.Client

    def get_by_web_id(self, web_id: str) -> PIAnalysisTemplate:
        """Look up an Analysis Template by its WebID.

        Calls ``GET /analysistemplates/{webId}``.

        Args:
            web_id: WebID of the analysis template.

        Returns:
            A :class:`PIAnalysisTemplate` populated from the API response.

        Raises:
            NotFoundError: If no analysis template with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"/analysistemplates/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)
        return PIAnalysisTemplate.model_validate(resp.json())

    def get_by_path(self, path: str) -> PIAnalysisTemplate:
        """Look up an Analysis Template by its full path.

        Calls ``GET /analysistemplates`` with a ``path`` query parameter.

        Args:
            path: Full AF path to the analysis template, e.g.
                ``"\\\\AF_SERVER\\DB\\ElementTemplates[Pump]"
                ``"\\AnalysisTemplates[FlowCalc]"``.

        Returns:
            A :class:`PIAnalysisTemplate` populated from the API response.

        Raises:
            NotFoundError: If no analysis template exists at the path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            "/analysistemplates", params={"path": path}
        )
        raise_for_response(resp)
        return PIAnalysisTemplate.model_validate(resp.json())

    def get_by_element_template(
        self,
        element_template_web_id: str,
    ) -> list[PIAnalysisTemplate]:
        """List analysis templates under an element template.

        Calls ``GET /elementtemplates/{webId}/analysistemplates``.

        Args:
            element_template_web_id: WebID of the parent element template.

        Returns:
            A list of :class:`PIAnalysisTemplate` objects.

        Raises:
            NotFoundError: If the element template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(element_template_web_id, "element_template_web_id")
        resp = self._client.get(
            f"/elementtemplates/"
            f"{quote(element_template_web_id, safe='')}"
            f"/analysistemplates"
        )
        raise_for_response(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [PIAnalysisTemplate.model_validate(item) for item in items]

    def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an Analysis Template.

        Calls ``PATCH /analysistemplates/{webId}``.

        Args:
            web_id: WebID of the analysis template.
            body: Fields to update (e.g. ``{"Description": "new desc"}``).

        Raises:
            NotFoundError: If the analysis template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"/analysistemplates/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete an Analysis Template.

        Calls ``DELETE /analysistemplates/{webId}``.

        Caution: deleting an analysis template may remove auto-created
        analyses from all derived elements.

        Args:
            web_id: WebID of the analysis template.

        Raises:
            NotFoundError: If the analysis template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"/analysistemplates/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class AsyncAnalysisTemplatesMixin:
    """Async methods for Analysis Template operations."""

    _client: httpx.AsyncClient

    async def get_by_web_id(self, web_id: str) -> PIAnalysisTemplate:
        """Look up an Analysis Template by its WebID.

        Calls ``GET /analysistemplates/{webId}``.

        Args:
            web_id: WebID of the analysis template.

        Returns:
            A :class:`PIAnalysisTemplate` populated from the API response.

        Raises:
            NotFoundError: If no analysis template with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"/analysistemplates/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
        return PIAnalysisTemplate.model_validate(resp.json())

    async def get_by_path(self, path: str) -> PIAnalysisTemplate:
        """Look up an Analysis Template by its full path.

        Calls ``GET /analysistemplates`` with a ``path`` query parameter.

        Args:
            path: Full AF path to the analysis template.

        Returns:
            A :class:`PIAnalysisTemplate` populated from the API response.

        Raises:
            NotFoundError: If no analysis template exists at the path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            "/analysistemplates", params={"path": path}
        )
        await raise_for_response_async(resp)
        return PIAnalysisTemplate.model_validate(resp.json())

    async def get_by_element_template(
        self,
        element_template_web_id: str,
    ) -> list[PIAnalysisTemplate]:
        """List analysis templates under an element template.

        Calls ``GET /elementtemplates/{webId}/analysistemplates``.

        Args:
            element_template_web_id: WebID of the parent element template.

        Returns:
            A list of :class:`PIAnalysisTemplate` objects.

        Raises:
            NotFoundError: If the element template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(element_template_web_id, "element_template_web_id")
        resp = await self._client.get(
            f"/elementtemplates/"
            f"{quote(element_template_web_id, safe='')}"
            f"/analysistemplates"
        )
        await raise_for_response_async(resp)
        data = resp.json()
        items: list[dict[str, Any]] = (
            data.get("Items", []) if isinstance(data, dict) else data
        )
        return [PIAnalysisTemplate.model_validate(item) for item in items]

    async def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update an Analysis Template.

        Calls ``PATCH /analysistemplates/{webId}``.

        Args:
            web_id: WebID of the analysis template.
            body: Fields to update (e.g. ``{"Description": "new desc"}``).

        Raises:
            NotFoundError: If the analysis template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"/analysistemplates/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete an Analysis Template.

        Calls ``DELETE /analysistemplates/{webId}``.

        Caution: deleting an analysis template may remove auto-created
        analyses from all derived elements.

        Args:
            web_id: WebID of the analysis template.

        Raises:
            NotFoundError: If the analysis template WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"/analysistemplates/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
