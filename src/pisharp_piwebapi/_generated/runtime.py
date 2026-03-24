"""Runtime helpers shared by generated API modules.

These utilities provide the base client, request building, and response
parsing that generated endpoint wrappers delegate to.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx  # noqa: TCH002

if TYPE_CHECKING:
    from collections.abc import Mapping


class GeneratedClient:
    """Low-level HTTP client used by generated endpoint wrappers.

    This wraps an ``httpx.Client`` and provides convenience methods
    for issuing API calls with consistent serialization and error handling.

    Typically you won't instantiate this directly — the high-level
    ``PIWebAPIClient`` can expose it via ``client.api``.
    """

    def __init__(self, http_client: httpx.Client) -> None:
        self._client = http_client

    # -- request helpers --------------------------------------------------

    def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        resp = self._client.get(path, params=dict(params) if params else None)
        resp.raise_for_status()
        return resp.json()

    def post(
        self,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        resp = self._client.post(
            path,
            json=json,
            params=dict(params) if params else None,
        )
        resp.raise_for_status()
        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return None

    def put(
        self,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        resp = self._client.put(
            path,
            json=json,
            params=dict(params) if params else None,
        )
        resp.raise_for_status()
        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return None

    def delete(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        resp = self._client.delete(path, params=dict(params) if params else None)
        resp.raise_for_status()
        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return None

    def patch(
        self,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        resp = self._client.patch(
            path,
            json=json,
            params=dict(params) if params else None,
        )
        resp.raise_for_status()
        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return None
