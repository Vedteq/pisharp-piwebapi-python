"""Batch request support for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import httpx


class BatchMixin:
    """Methods for batch requests. Mixed into client classes."""

    _client: httpx.Client

    def execute_batch(self, requests: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Execute a batch of PI Web API requests in a single HTTP call.

        Args:
            requests: Dict mapping request IDs to request definitions.
                Each request should have "Method" and "Resource" keys,
                and optionally "Content", "Headers", "ParentIds".

                Example::

                    {
                        "1": {"Method": "GET", "Resource": "/points?path=\\\\SERVER\\\\sinusoid"},
                        "2": {"Method": "GET", "Resource": "/streams/{0}/value", "ParentIds": ["1"]},
                    }

        Returns:
            Dict mapping request IDs to response objects with
            "Status", "Headers", and "Content" keys.
        """
        resp = self._client.post("/batch", json=requests)
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]


class AsyncBatchMixin:
    """Async methods for batch requests."""

    _client: httpx.AsyncClient  # type: ignore[assignment]

    async def execute_batch(self, requests: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Execute a batch of PI Web API requests (async)."""
        resp = await self._client.post("/batch", json=requests)
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
