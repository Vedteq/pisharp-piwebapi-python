"""Indexed AF Search operations for PI Web API.

The ``/search/query`` endpoint provides fast full-text search across
AF objects (elements, event frames, attributes) using the AF indexer.
This is significantly faster than hierarchy traversal for large AF
databases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pisharp_piwebapi.exceptions import (
    raise_for_response,
    raise_for_response_async,
    validate_web_id,
)

if TYPE_CHECKING:
    import httpx


class SearchResult:
    """A single result from an indexed AF search.

    The PI Web API search endpoint returns heterogeneous objects
    (elements, event frames, attributes, etc.), so this wrapper
    provides a uniform interface to the common fields while
    preserving the full raw response for type-specific access.

    Attributes:
        web_id: The WebID of the matched object.
        name: The display name.
        path: The full AF path.
        item_type: The PI Web API object type
            (e.g. ``"Element"``, ``"EventFrame"``).
        score: Relevance score assigned by the search engine.
        raw: The complete raw dict from the API response.
    """

    __slots__ = ("web_id", "name", "path", "item_type", "score", "raw")

    def __init__(self, data: dict[str, Any]) -> None:
        self.raw: dict[str, Any] = data
        self.web_id: str = data.get("WebId", "")
        self.name: str = data.get("Name", "")
        self.path: str = data.get("Path", "")
        self.item_type: str = data.get("ItemType", "")
        self.score: float = data.get("Score", 0.0)

    def __repr__(self) -> str:
        return (
            f"SearchResult(name={self.name!r}, "
            f"item_type={self.item_type!r}, "
            f"web_id={self.web_id!r})"
        )


class SearchMixin:
    """Methods for indexed AF search via ``/search/query``.

    Mixed into the sync client class.
    """

    _client: httpx.Client

    def query(
        self,
        q: str,
        *,
        scope: str | None = None,
        fields: str | None = None,
        max_count: int = 100,
        start_index: int = 0,
    ) -> list[SearchResult]:
        """Run an indexed AF search query.

        Calls ``GET /search/query?q=...``.  The query uses the AF
        indexed search syntax which supports field-scoped terms like
        ``name:Pump*``, ``templateName:Equipment``,
        ``attributeName:Temperature``, and boolean operators.

        Args:
            q: The search query string.  Supports PI AF indexed
                search syntax, e.g.:

                - ``"Pump*"`` — name wildcard
                - ``"name:Pump* templateName:Equipment"`` — scoped
                - ``"name:Pump* AND attributeName:Status"`` — boolean

            scope: Optional AF database WebID to restrict the search
                scope.  If omitted, all databases are searched.
            fields: Optional comma-separated list of fields to return
                in results (e.g. ``"Name,WebId,Path"``).
            max_count: Maximum number of results. Defaults to ``100``.
            start_index: Starting index for pagination. Defaults to
                ``0``.

        Returns:
            List of :class:`SearchResult` objects.

        Raises:
            PIWebAPIError: If the query is malformed or the server
                returns a non-2xx response.
        """
        params: dict[str, str | int] = {
            "q": q,
            "count": max_count,
            "start": start_index,
        }
        if scope is not None:
            validate_web_id(scope, "scope")
            params["scope"] = scope
        if fields is not None:
            params["fields"] = fields
        resp = self._client.get("/search/query", params=params)
        raise_for_response(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [SearchResult(item) for item in items]


class AsyncSearchMixin:
    """Async methods for indexed AF search.

    Mixed into the async client class.
    """

    _client: httpx.AsyncClient

    async def query(
        self,
        q: str,
        *,
        scope: str | None = None,
        fields: str | None = None,
        max_count: int = 100,
        start_index: int = 0,
    ) -> list[SearchResult]:
        """Run an indexed AF search query.

        Calls ``GET /search/query?q=...``.  See :meth:`SearchMixin.query`
        for full documentation of the query syntax and parameters.

        Args:
            q: The search query string.
            scope: Optional AF database WebID to restrict scope.
            fields: Optional comma-separated list of return fields.
            max_count: Maximum number of results. Defaults to ``100``.
            start_index: Starting index for pagination. Defaults to
                ``0``.

        Returns:
            List of :class:`SearchResult` objects.

        Raises:
            PIWebAPIError: If the query is malformed or the server
                returns a non-2xx response.
        """
        params: dict[str, str | int] = {
            "q": q,
            "count": max_count,
            "start": start_index,
        }
        if scope is not None:
            validate_web_id(scope, "scope")
            params["scope"] = scope
        if fields is not None:
            params["fields"] = fields
        resp = await self._client.get("/search/query", params=params)
        await raise_for_response_async(resp)
        data = resp.json()
        items = data.get("Items", []) if isinstance(data, dict) else data
        return [SearchResult(item) for item in items]
