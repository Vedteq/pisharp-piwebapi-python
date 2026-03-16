"""Main PI Web API client classes — sync and async."""

from __future__ import annotations

import ssl
from typing import Any

import httpx

from pisharp_piwebapi.auth import basic_auth, kerberos_auth
from pisharp_piwebapi.batch import AsyncBatchMixin, BatchMixin
from pisharp_piwebapi.elements import AsyncElementsMixin, ElementsMixin
from pisharp_piwebapi.eventframes import AsyncEventFramesMixin, EventFramesMixin
from pisharp_piwebapi.exceptions import (
    AuthenticationError,
    NotFoundError,
    PIWebAPIError,
    RateLimitError,
    ServerError,
)
from pisharp_piwebapi.pagination import AsyncPaginationMixin, PaginationMixin
from pisharp_piwebapi.points import AsyncPointsMixin, PointsMixin
from pisharp_piwebapi.servers import (
    AssetServersMixin,
    AsyncAssetServersMixin,
    AsyncDatabasesMixin,
    AsyncDataServersMixin,
    DatabasesMixin,
    DataServersMixin,
)
from pisharp_piwebapi.values import AsyncStreamsMixin, StreamsMixin


def _build_event_hooks() -> dict[str, list[Any]]:
    """Build httpx event hooks for error handling."""

    def _raise_on_error(response: httpx.Response) -> None:
        if response.is_success:
            return
        response.read()
        status = response.status_code
        try:
            body = response.json()
        except Exception:
            body = response.text

        message = f"PI Web API error {status}"
        if isinstance(body, dict) and "Message" in body:
            message = body["Message"]

        if status in (401, 403):
            raise AuthenticationError(message, status_code=status, body=body)
        elif status == 404:
            raise NotFoundError(message, status_code=status, body=body)
        elif status == 429:
            raise RateLimitError(message, status_code=status, body=body)
        elif status >= 500:
            raise ServerError(message, status_code=status, body=body)
        else:
            raise PIWebAPIError(message, status_code=status, body=body)

    return {"response": [_raise_on_error]}


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
        self._client = client  # type: ignore[assignment]


class _ElementsAccessor(ElementsMixin):
    """Namespace for element operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _EventFramesAccessor(EventFramesMixin):
    """Namespace for event frame operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncStreamsAccessor(AsyncStreamsMixin):
    """Namespace for stream operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client  # type: ignore[assignment]


class _AsyncElementsAccessor(AsyncElementsMixin):
    """Namespace for element operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client  # type: ignore[assignment]


class _AssetServersAccessor(AssetServersMixin):
    """Namespace for asset server operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _DataServersAccessor(DataServersMixin):
    """Namespace for data server operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _DatabasesAccessor(DatabasesMixin):
    """Namespace for database operations on the sync client."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class _AsyncEventFramesAccessor(AsyncEventFramesMixin):
    """Namespace for event frame operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client  # type: ignore[assignment]


class _AsyncAssetServersAccessor(AsyncAssetServersMixin):
    """Namespace for asset server operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client  # type: ignore[assignment]


class _AsyncDataServersAccessor(AsyncDataServersMixin):
    """Namespace for data server operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client  # type: ignore[assignment]


class _AsyncDatabasesAccessor(AsyncDatabasesMixin):
    """Namespace for database operations on the async client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client  # type: ignore[assignment]


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
        self.elements = _ElementsAccessor(self._client)
        self.eventframes = _EventFramesAccessor(self._client)
        self.assetservers = _AssetServersAccessor(self._client)
        self.dataservers = _DataServersAccessor(self._client)
        self.databases = _DatabasesAccessor(self._client)

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
        )
        self.points = _AsyncPointsAccessor(self._client)
        self.streams = _AsyncStreamsAccessor(self._client)
        self.elements = _AsyncElementsAccessor(self._client)
        self.eventframes = _AsyncEventFramesAccessor(self._client)
        self.assetservers = _AsyncAssetServersAccessor(self._client)
        self.dataservers = _AsyncDataServersAccessor(self._client)
        self.databases = _AsyncDatabasesAccessor(self._client)

    async def aclose(self) -> None:
        """Close the underlying HTTP connection."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncPIWebAPIClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
