"""Category operations for PI Web API (element, analysis, attribute).

All three category types share the same API shape, so this module
provides a generic mixin parameterized by the URL prefix.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)
from pisharp_piwebapi.models import PICategory

if TYPE_CHECKING:
    import httpx


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


class _CategoryMixinBase:
    """Shared helpers for sync category mixins."""

    _client: httpx.Client
    _prefix: str  # e.g. "/elementcategories"

    def get_by_web_id(self, web_id: str) -> PICategory:
        """Look up a category by its WebID.

        Args:
            web_id: WebID of the category.

        Returns:
            A :class:`PICategory` populated from the API response.

        Raises:
            NotFoundError: If no category with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.get(
            f"{self._prefix}/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)
        return PICategory.model_validate(resp.json())

    def get_by_path(self, path: str) -> PICategory:
        """Look up a category by its full path.

        Args:
            path: Full AF path to the category.

        Returns:
            A :class:`PICategory` populated from the API response.

        Raises:
            NotFoundError: If no category exists at the given path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = self._client.get(
            self._prefix, params={"path": path}
        )
        raise_for_response(resp)
        return PICategory.model_validate(resp.json())

    def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a category.

        Calls ``PATCH /{prefix}/{webId}``.

        Note: PI Web API does not allow renaming categories via PATCH;
        only the description can be changed.

        Args:
            web_id: WebID of the category.
            body: Fields to update (e.g. ``{"Description": "updated"}``).

        Raises:
            NotFoundError: If the category WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.patch(
            f"{self._prefix}/{quote(web_id, safe='')}",
            json=body,
        )
        raise_for_response(resp)

    def delete(self, web_id: str) -> None:
        """Delete a category.

        Calls ``DELETE /{prefix}/{webId}``.

        Args:
            web_id: WebID of the category.

        Raises:
            NotFoundError: If the category WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = self._client.delete(
            f"{self._prefix}/{quote(web_id, safe='')}"
        )
        raise_for_response(resp)


class ElementCategoriesMixin(_CategoryMixinBase):
    """Methods for Element Category operations. Mixed into the sync client.

    Calls ``GET/PATCH/DELETE /elementcategories/{webId}``.
    """

    _prefix = "/elementcategories"


class AnalysisCategoriesMixin(_CategoryMixinBase):
    """Methods for Analysis Category operations. Mixed into the sync client.

    Calls ``GET/PATCH/DELETE /analysiscategories/{webId}``.
    """

    _prefix = "/analysiscategories"


class AttributeCategoriesMixin(_CategoryMixinBase):
    """Methods for Attribute Category operations. Mixed into the sync client.

    Calls ``GET/PATCH/DELETE /attributecategories/{webId}``.
    """

    _prefix = "/attributecategories"


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------


class _AsyncCategoryMixinBase:
    """Shared helpers for async category mixins."""

    _client: httpx.AsyncClient
    _prefix: str

    async def get_by_web_id(self, web_id: str) -> PICategory:
        """Look up a category by its WebID.

        Args:
            web_id: WebID of the category.

        Returns:
            A :class:`PICategory` populated from the API response.

        Raises:
            NotFoundError: If no category with the given WebID exists.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.get(
            f"{self._prefix}/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)
        return PICategory.model_validate(resp.json())

    async def get_by_path(self, path: str) -> PICategory:
        """Look up a category by its full path.

        Args:
            path: Full AF path to the category.

        Returns:
            A :class:`PICategory` populated from the API response.

        Raises:
            NotFoundError: If no category exists at the given path.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        resp = await self._client.get(
            self._prefix, params={"path": path}
        )
        await raise_for_response_async(resp)
        return PICategory.model_validate(resp.json())

    async def update(
        self,
        web_id: str,
        body: dict[str, Any],
    ) -> None:
        """Update a category.

        Calls ``PATCH /{prefix}/{webId}``.

        Args:
            web_id: WebID of the category.
            body: Fields to update (e.g. ``{"Description": "updated"}``).

        Raises:
            NotFoundError: If the category WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.patch(
            f"{self._prefix}/{quote(web_id, safe='')}",
            json=body,
        )
        await raise_for_response_async(resp)

    async def delete(self, web_id: str) -> None:
        """Delete a category.

        Calls ``DELETE /{prefix}/{webId}``.

        Args:
            web_id: WebID of the category.

        Raises:
            NotFoundError: If the category WebID is invalid.
            AuthenticationError: If the request is rejected as unauthorized.
            PIWebAPIError: For any other non-2xx response.
        """
        validate_web_id(web_id)
        resp = await self._client.delete(
            f"{self._prefix}/{quote(web_id, safe='')}"
        )
        await raise_for_response_async(resp)


class AsyncElementCategoriesMixin(_AsyncCategoryMixinBase):
    """Async methods for Element Category operations.

    Calls ``GET/PATCH/DELETE /elementcategories/{webId}``.
    """

    _prefix = "/elementcategories"


class AsyncAnalysisCategoriesMixin(_AsyncCategoryMixinBase):
    """Async methods for Analysis Category operations.

    Calls ``GET/PATCH/DELETE /analysiscategories/{webId}``.
    """

    _prefix = "/analysiscategories"


class AsyncAttributeCategoriesMixin(_AsyncCategoryMixinBase):
    """Async methods for Attribute Category operations.

    Calls ``GET/PATCH/DELETE /attributecategories/{webId}``.
    """

    _prefix = "/attributecategories"
