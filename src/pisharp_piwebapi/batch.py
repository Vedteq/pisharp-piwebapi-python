"""Batch request support for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pisharp_piwebapi.exceptions import raise_for_response, raise_for_response_async

if TYPE_CHECKING:
    import httpx


class BatchMixin:
    """Methods for batch requests. Mixed into the sync client class."""

    _client: httpx.Client

    def execute_batch(self, requests: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Execute a batch of PI Web API requests in a single HTTP call.

        PI Web API batch requests allow multiple sub-requests to be sent in one
        round-trip.  Sub-requests can reference the output of earlier requests
        using ``"ParentIds"`` to express dependencies.

        Args:
            requests: Dict mapping request IDs to request definitions.
                Each entry must have ``"Method"`` and ``"Resource"`` keys, and
                optionally ``"Content"``, ``"Headers"``, and ``"ParentIds"``.

                Example::

                    {
                        "1": {
                            "Method": "GET",
                            "Resource": "/points?path=\\\\\\\\SERVER\\\\sinusoid",
                        },
                        "2": {
                            "Method": "GET",
                            "Resource": "/streams/{0}/value",
                            "ParentIds": ["1"],
                        },
                    }

        Returns:
            Dict mapping request IDs to response objects.  Each value has
            ``"Status"`` (int), ``"Headers"`` (dict), and ``"Content"`` keys.

        Raises:
            AuthenticationError: If the outer batch request is rejected.
            ServerError: If the server returns a 5xx for the outer request.
            PIWebAPIError: For any other non-2xx outer response.
        """
        resp = self._client.post("/batch", json=requests)
        raise_for_response(resp)
        return resp.json()  # type: ignore[no-any-return]


class AsyncBatchMixin:
    """Async methods for batch requests. Mixed into the async client class."""

    _client: httpx.AsyncClient

    async def execute_batch(self, requests: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Execute a batch of PI Web API requests in a single HTTP call.

        Args:
            requests: Dict mapping request IDs to request definitions.
                Each entry must have ``"Method"`` and ``"Resource"`` keys, and
                optionally ``"Content"``, ``"Headers"``, and ``"ParentIds"``.

        Returns:
            Dict mapping request IDs to response objects.  Each value has
            ``"Status"`` (int), ``"Headers"`` (dict), and ``"Content"`` keys.

        Raises:
            AuthenticationError: If the outer batch request is rejected.
            ServerError: If the server returns a 5xx for the outer request.
            PIWebAPIError: For any other non-2xx outer response.
        """
        resp = await self._client.post("/batch", json=requests)
        await raise_for_response_async(resp)
        return resp.json()  # type: ignore[no-any-return]
