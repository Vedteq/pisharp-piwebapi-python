"""Main PI Web API client classes — sync and async."""

from __future__ import annotations

import ssl
from typing import Any

import httpx

from pisharp_piwebapi.auth import basic_auth, kerberos_auth
from pisharp_piwebapi.batch import AsyncBatchMixin, BatchMixin
from pisharp_piwebapi.exceptions import raise_for_response, raise_for_response_async
from pisharp_piwebapi.pagination import AsyncPaginationMixin, PaginationMixin
from pisharp_piwebapi.points import AsyncPointsMixin, PointsMixin
from pisharp_piwebapi.values import AsyncStreamsMixin, StreamsMixin


def _build_event_hooks() -> dict[str, list[Any]]:
    """Build httpx sync event hooks for error handling."""

    def _raise_on_error(response: httpx.Response) -> None:
        response.read()  # Ensure body is loaded before inspecting it in the hook
        raise_for_response(response)

    return {"response": [_raise_on_error]}


def _build_async_event_hooks() -> dict[str, list[Any]]:
    """Build httpx async event hooks for error handling."""

    async def _raise_on_error_async(response: httpx.Response) -> None:
        await raise_for_response_async(response)

    return {"response": [_raise_on_error_async]}


class _PointsAccessor(PointsMixin):
    """Namespace for point operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _StreamsAccessor(StreamsMixin):
    """Namespace for stream operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncPointsAccessor(AsyncPointsMixin):
    """Namespace for point operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class _AsyncStreamsAccessor(AsyncStreamsMixin):
    """Namespace for stream operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client


class PIWebAPIClient(BatchMixin, PaginationMixin):
    """Synchronous PI Web API client.

    Usage::

        client = PIWebAPIClient(
            base_url="https://your-server/piwebapi",
            username="user",
            password="pass",
        )
        point = client.points.get_by_path(r"\\\\SERVER\\sinusoid")
        value = client.streams.get_value(point.web_id)
    """

    def __init__(
        self,
        base_url: str,
        *,
        username: str | None = None,
        password: str | None = None,
        auth_method: str = "basic",
        verify_ssl: bool = True,
        cert: str | tuple[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the PI Web API client.

        Args:
            base_url: PI Web API base URL (e.g. "https://server/piwebapi").
            username: Username for Basic auth.
            password: Password for Basic auth.
            auth_method: Authentication method ("basic" or "kerberos").
            verify_ssl: Whether to verify SSL certificates.
            cert: Client certificate path or (cert, key) tuple.
            timeout: Request timeout in seconds.
        """
        auth: httpx.Auth | None = None
        if auth_method == "kerberos":
            auth = kerberos_auth()
        elif username and password:
            auth = basic_auth(username, password)

        ssl_context: ssl.SSLContext | bool = verify_ssl
        if cert:
            ssl_context = ssl.create_default_context()
            if isinstance(cert, tuple):
                ssl_context.load_cert_chain(cert[0], cert[1])
            else:
                ssl_context.load_cert_chain(cert)

        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            auth=auth,
            verify=ssl_context,
            timeout=timeout,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            event_hooks=_build_event_hooks(),
        )
        self.points = _PointsAccessor(self._client)
        self.streams = _StreamsAccessor(self._client)

    def close(self) -> None:
        """Close the underlying HTTP connection."""
        self._client.close()

    def __enter__(self) -> PIWebAPIClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncPIWebAPIClient(AsyncBatchMixin, AsyncPaginationMixin):
    """Asynchronous PI Web API client.

    Usage::

        async with AsyncPIWebAPIClient(
            base_url="https://your-server/piwebapi",
            username="user",
            password="pass",
        ) as client:
            point = await client.points.get_by_path(r"\\\\SERVER\\sinusoid")
            value = await client.streams.get_value(point.web_id)
    """

    def __init__(
        self,
        base_url: str,
        *,
        username: str | None = None,
        password: str | None = None,
        auth_method: str = "basic",
        verify_ssl: bool = True,
        cert: str | tuple[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the async PI Web API client.

        Args:
            base_url: PI Web API base URL (e.g. "https://server/piwebapi").
            username: Username for Basic auth.
            password: Password for Basic auth.
            auth_method: Authentication method ("basic" or "kerberos").
            verify_ssl: Whether to verify SSL certificates.
            cert: Client certificate path or (cert, key) tuple.
            timeout: Request timeout in seconds.
        """
        auth: httpx.Auth | None = None
        if auth_method == "kerberos":
            auth = kerberos_auth()
        elif username and password:
            auth = basic_auth(username, password)

        ssl_context: ssl.SSLContext | bool = verify_ssl
        if cert:
            ssl_context = ssl.create_default_context()
            if isinstance(cert, tuple):
                ssl_context.load_cert_chain(cert[0], cert[1])
            else:
                ssl_context.load_cert_chain(cert)

        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            auth=auth,
            verify=ssl_context,
            timeout=timeout,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            event_hooks=_build_async_event_hooks(),
        )
        self.points = _AsyncPointsAccessor(self._client)
        self.streams = _AsyncStreamsAccessor(self._client)

    async def aclose(self) -> None:
        """Close the underlying HTTP connection."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncPIWebAPIClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
