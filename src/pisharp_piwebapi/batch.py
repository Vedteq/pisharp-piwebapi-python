"""Batch request support for PI Web API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pisharp_piwebapi.exceptions import (
    BatchError,
    raise_for_response,
    raise_for_response_async,
)

if TYPE_CHECKING:
    import httpx

_ALLOWED_BATCH_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})


def _validate_batch_requests(requests: dict[str, dict[str, Any]]) -> None:
    """Validate batch sub-request definitions before sending.

    Checks that each sub-request has a valid HTTP method and a relative
    resource path.  This prevents SSRF via absolute URLs and rejects
    unexpected HTTP verbs.

    Args:
        requests: The batch request dict to validate.

    Raises:
        ValueError: If any sub-request has an invalid method or a
            non-relative resource path.
    """
    for req_id, req in requests.items():
        method = req.get("Method", "")
        if method not in _ALLOWED_BATCH_METHODS:
            raise ValueError(
                f"Batch request {req_id!r}: invalid method {method!r}. "
                f"Must be one of {sorted(_ALLOWED_BATCH_METHODS)}."
            )
        resource = req.get("Resource", "")
        if not resource.startswith("/") or resource.startswith("//"):
            raise ValueError(
                f"Batch request {req_id!r}: Resource must be a single-slash "
                f"relative path (e.g. '/streams/{{webId}}/value'). "
                f"Got {resource!r}."
            )


def _check_batch_errors(data: dict[str, Any]) -> None:
    """Inspect batch sub-responses and raise :class:`BatchError` on failures.

    A sub-request is considered failed if its ``"Status"`` field is not
    in the 2xx range.  When one or more sub-requests fail, a
    :class:`BatchError` is raised that includes the failing request IDs,
    status codes, and any error content.

    Args:
        data: The parsed JSON response from ``POST /batch``.

    Raises:
        BatchError: If any sub-request has a non-2xx status code.
    """
    errors: list[dict[str, Any]] = []
    for req_id, resp_item in data.items():
        if not isinstance(resp_item, dict):
            continue
        status = resp_item.get("Status", 0)
        if not (200 <= status < 300):
            errors.append({
                "RequestId": req_id,
                "Status": status,
                "Content": resp_item.get("Content"),
            })
    if errors:
        failed_ids = [e["RequestId"] for e in errors]
        raise BatchError(
            f"Batch sub-request(s) {', '.join(failed_ids)} failed",
            errors=errors,
        )


class BatchMixin:
    """Methods for batch requests. Mixed into the sync client class."""

    _client: httpx.Client

    def execute_batch(
        self,
        requests: dict[str, dict[str, Any]],
        *,
        raise_on_errors: bool = True,
    ) -> dict[str, Any]:
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

            raise_on_errors: When ``True`` (the default), inspect each
                sub-response and raise :class:`BatchError` if any
                sub-request returned a non-2xx status.  Set to ``False``
                to get the raw response dict and handle errors yourself.

        Returns:
            Dict mapping request IDs to response objects.  Each value has
            ``"Status"`` (int), ``"Headers"`` (dict), and ``"Content"`` keys.

        Raises:
            BatchError: If *raise_on_errors* is ``True`` and any
                sub-request returned a non-2xx status.
            AuthenticationError: If the outer batch request is rejected.
            ServerError: If the server returns a 5xx for the outer request.
            PIWebAPIError: For any other non-2xx outer response.
            ValueError: If any sub-request has an invalid method or
                absolute resource URL.
        """
        _validate_batch_requests(requests)
        resp = self._client.post("/batch", json=requests)
        raise_for_response(resp)
        data: dict[str, Any] = resp.json()
        if raise_on_errors:
            _check_batch_errors(data)
        return data


class AsyncBatchMixin:
    """Async methods for batch requests. Mixed into the async client class."""

    _client: httpx.AsyncClient

    async def execute_batch(
        self,
        requests: dict[str, dict[str, Any]],
        *,
        raise_on_errors: bool = True,
    ) -> dict[str, Any]:
        """Execute a batch of PI Web API requests in a single HTTP call.

        Args:
            requests: Dict mapping request IDs to request definitions.
                Each entry must have ``"Method"`` and ``"Resource"`` keys, and
                optionally ``"Content"``, ``"Headers"``, and ``"ParentIds"``.

            raise_on_errors: When ``True`` (the default), inspect each
                sub-response and raise :class:`BatchError` if any
                sub-request returned a non-2xx status.  Set to ``False``
                to get the raw response dict and handle errors yourself.

        Returns:
            Dict mapping request IDs to response objects.  Each value has
            ``"Status"`` (int), ``"Headers"`` (dict), and ``"Content"`` keys.

        Raises:
            BatchError: If *raise_on_errors* is ``True`` and any
                sub-request returned a non-2xx status.
            AuthenticationError: If the outer batch request is rejected.
            ServerError: If the server returns a 5xx for the outer request.
            PIWebAPIError: For any other non-2xx outer response.
            ValueError: If any sub-request has an invalid method or
                absolute resource URL.
        """
        _validate_batch_requests(requests)
        resp = await self._client.post("/batch", json=requests)
        await raise_for_response_async(resp)
        data: dict[str, Any] = resp.json()
        if raise_on_errors:
            _check_batch_errors(data)
        return data
