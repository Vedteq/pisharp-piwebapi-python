"""Pagination helpers for PI Web API responses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from pisharp_piwebapi.exceptions import PIWebAPIError, raise_for_response, raise_for_response_async

if TYPE_CHECKING:
    import httpx


def _same_origin(base_url: str, next_url: str) -> bool:
    """Check that *next_url* shares the same scheme and host as *base_url*.

    This prevents SSRF attacks where a malicious server returns a
    ``Links.Next`` pointing at an internal network address.
    """
    base = urlparse(base_url)
    target = urlparse(next_url)
    return (base.scheme, base.netloc) == (target.scheme, target.netloc)


class PaginationMixin:
    """Helpers for paginated API responses. Mixed into the sync client class."""

    _client: httpx.Client

    def get_all_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        max_pages: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of a paginated PI Web API response.

        Follows ``Links.Next`` in each response until there are no more pages
        or ``max_pages`` is reached.

        Args:
            path: API path for the first request (e.g. ``"/points/search"``).
            params: Query parameters for the initial request only.
                Subsequent pages are fetched via the full ``Links.Next`` URL so
                params are not forwarded to them.
            max_pages: Safety limit on the number of pages to fetch.
                Defaults to ``100``.

        Returns:
            Combined list of all ``"Items"`` dicts across all pages.

        Raises:
            AuthenticationError: If any request is rejected as unauthorized.
            PIWebAPIError: If a pagination URL points to a different origin
                (potential SSRF), or for any other non-2xx response.
        """
        all_items: list[dict[str, Any]] = []
        current_params = dict(params) if params else {}
        url: str | None = path

        for _ in range(max_pages):
            if url is None:
                break

            if url.startswith("http"):
                if not _same_origin(str(self._client.base_url), url):
                    raise PIWebAPIError(
                        "Pagination URL origin mismatch — refusing to "
                        "follow a URL that points to a different server."
                    )
                resp = self._client.get(url)
            else:
                resp = self._client.get(url, params=current_params)
                current_params = {}  # Only apply params on the first request

            raise_for_response(resp)
            data = resp.json()

            items = data.get("Items", [])
            all_items.extend(items)

            links = data.get("Links", {})
            url = links.get("Next")

        return all_items


class AsyncPaginationMixin:
    """Async helpers for paginated API responses. Mixed into the async client class."""

    _client: httpx.AsyncClient

    async def get_all_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        max_pages: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of a paginated PI Web API response.

        Follows ``Links.Next`` in each response until there are no more pages
        or ``max_pages`` is reached.

        Args:
            path: API path for the first request (e.g. ``"/points/search"``).
            params: Query parameters for the initial request only.
            max_pages: Safety limit on the number of pages to fetch.
                Defaults to ``100``.

        Returns:
            Combined list of all ``"Items"`` dicts across all pages.

        Raises:
            AuthenticationError: If any request is rejected as unauthorized.
            PIWebAPIError: If a pagination URL points to a different origin
                (potential SSRF), or for any other non-2xx response.
        """
        all_items: list[dict[str, Any]] = []
        current_params = dict(params) if params else {}
        url: str | None = path

        for _ in range(max_pages):
            if url is None:
                break

            if url.startswith("http"):
                if not _same_origin(str(self._client.base_url), url):
                    raise PIWebAPIError(
                        "Pagination URL origin mismatch — refusing to "
                        "follow a URL that points to a different server."
                    )
                resp = await self._client.get(url)
            else:
                resp = await self._client.get(url, params=current_params)
                current_params = {}

            await raise_for_response_async(resp)
            data = resp.json()

            items = data.get("Items", [])
            all_items.extend(items)

            links = data.get("Links", {})
            url = links.get("Next")

        return all_items
