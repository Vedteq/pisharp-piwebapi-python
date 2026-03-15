"""Pagination helpers for PI Web API responses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import httpx


class PaginationMixin:
    """Helpers for paginated API responses. Mixed into client classes."""

    _client: httpx.Client

    def get_all_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        max_pages: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of a paginated PI Web API response.

        Follows the "Links.Next" URL in each response to collect all items.

        Args:
            path: API path (e.g. "/points/search").
            params: Query parameters for the initial request.
            max_pages: Safety limit on number of pages to fetch.

        Returns:
            Combined list of all "Items" across all pages.
        """
        all_items: list[dict[str, Any]] = []
        current_params = dict(params) if params else {}
        url: str | None = path

        for _ in range(max_pages):
            if url is None:
                break

            if url.startswith("http"):
                resp = self._client.get(url)
            else:
                resp = self._client.get(url, params=current_params)
                current_params = {}  # Only use params on first request

            resp.raise_for_status()
            data = resp.json()

            items = data.get("Items", [])
            all_items.extend(items)

            links = data.get("Links", {})
            url = links.get("Next")

        return all_items


class AsyncPaginationMixin:
    """Async helpers for paginated API responses."""

    _client: httpx.AsyncClient  # type: ignore[assignment]

    async def get_all_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        max_pages: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of a paginated response (async)."""
        all_items: list[dict[str, Any]] = []
        current_params = dict(params) if params else {}
        url: str | None = path

        for _ in range(max_pages):
            if url is None:
                break

            if url.startswith("http"):
                resp = await self._client.get(url)
            else:
                resp = await self._client.get(url, params=current_params)
                current_params = {}

            resp.raise_for_status()
            data = resp.json()

            items = data.get("Items", [])
            all_items.extend(items)

            links = data.get("Links", {})
            url = links.get("Next")

        return all_items
