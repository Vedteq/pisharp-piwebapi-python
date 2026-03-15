"""Tests for PIWebAPIClient and AsyncPIWebAPIClient — construction and error hooks."""

from __future__ import annotations

import httpx
import pytest
import respx

from pisharp_piwebapi.client import AsyncPIWebAPIClient, PIWebAPIClient
from pisharp_piwebapi.exceptions import (
    AuthenticationError,
    NotFoundError,
    PIWebAPIError,
    RateLimitError,
    ServerError,
)

BASE = "https://piserver/piwebapi"


# ===========================================================================
# Client construction
# ===========================================================================


def test_sync_client_constructs() -> None:
    """PIWebAPIClient builds without error for basic auth."""
    client = PIWebAPIClient(BASE, username="user", password="pass")
    assert client._client is not None
    client.close()


def test_sync_client_context_manager() -> None:
    """PIWebAPIClient works as a context manager."""
    with PIWebAPIClient(BASE, username="user", password="pass") as client:
        assert client._client is not None


def test_async_client_constructs() -> None:
    """AsyncPIWebAPIClient builds without error."""
    client = AsyncPIWebAPIClient(BASE, username="user", password="pass")
    assert client._client is not None


def test_sync_client_exposes_points_and_streams() -> None:
    """The sync client exposes .points and .streams accessors."""
    with PIWebAPIClient(BASE, username="user", password="pass") as client:
        assert hasattr(client.points, "get_by_path")
        assert hasattr(client.streams, "get_value")


def test_async_client_exposes_points_and_streams() -> None:
    """The async client exposes .points and .streams accessors."""
    client = AsyncPIWebAPIClient(BASE, username="user", password="pass")
    assert hasattr(client.points, "get_by_path")
    assert hasattr(client.streams, "get_value")


# ===========================================================================
# Error-hook mapping — sync client raises the right SDK exception per status
# ===========================================================================


@respx.mock
def test_event_hook_401_raises_authentication_error() -> None:
    """A 401 response raises AuthenticationError via the event hook."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(401, json={"Message": "Unauthorized"})
    )

    with PIWebAPIClient(BASE, username="user", password="pass") as client:
        with pytest.raises(AuthenticationError) as exc_info:
            client._client.get("/points")

    assert exc_info.value.status_code == 401


@respx.mock
def test_event_hook_403_raises_authentication_error() -> None:
    """A 403 response raises AuthenticationError via the event hook."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(403, json={"Message": "Forbidden"})
    )

    with PIWebAPIClient(BASE, username="user", password="pass") as client:
        with pytest.raises(AuthenticationError) as exc_info:
            client._client.get("/points")

    assert exc_info.value.status_code == 403


@respx.mock
def test_event_hook_404_raises_not_found_error() -> None:
    """A 404 response raises NotFoundError via the event hook."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(404, json={"Message": "Point not found"})
    )

    with PIWebAPIClient(BASE, username="user", password="pass") as client:
        with pytest.raises(NotFoundError) as exc_info:
            client._client.get("/points")

    assert exc_info.value.status_code == 404
    assert "Point not found" in str(exc_info.value)


@respx.mock
def test_event_hook_429_raises_rate_limit_error() -> None:
    """A 429 response raises RateLimitError via the event hook."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(429, json={"Message": "Too many requests"})
    )

    with PIWebAPIClient(BASE, username="user", password="pass") as client:
        with pytest.raises(RateLimitError) as exc_info:
            client._client.get("/points")

    assert exc_info.value.status_code == 429


@respx.mock
def test_event_hook_500_raises_server_error() -> None:
    """A 500 response raises ServerError via the event hook."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(500, json={"Message": "Internal server error"})
    )

    with PIWebAPIClient(BASE, username="user", password="pass") as client:
        with pytest.raises(ServerError) as exc_info:
            client._client.get("/points")

    assert exc_info.value.status_code == 500


@respx.mock
def test_event_hook_400_raises_base_piwebapi_error() -> None:
    """A 400 response raises the base PIWebAPIError."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(400, json={"Message": "Bad request"})
    )

    with PIWebAPIClient(BASE, username="user", password="pass") as client:
        with pytest.raises(PIWebAPIError) as exc_info:
            client._client.get("/points")

    assert exc_info.value.status_code == 400


@respx.mock
def test_event_hook_uses_message_field_in_error() -> None:
    """The event hook extracts the 'Message' field from the response body."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(404, json={"Message": "Specific error text"})
    )

    with PIWebAPIClient(BASE, username="user", password="pass") as client:
        with pytest.raises(NotFoundError) as exc_info:
            client._client.get("/points")

    assert str(exc_info.value) == "Specific error text"


@respx.mock
def test_event_hook_non_json_body() -> None:
    """The event hook handles a non-JSON error body gracefully."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    with PIWebAPIClient(BASE, username="user", password="pass") as client:
        with pytest.raises(ServerError) as exc_info:
            client._client.get("/points")

    assert exc_info.value.status_code == 500
    assert exc_info.value.body == "Internal Server Error"


@respx.mock
def test_event_hook_200_does_not_raise() -> None:
    """A 200 response does not trigger any exception."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(200, json={"WebId": "P01", "Name": "test"})
    )

    with PIWebAPIClient(BASE, username="user", password="pass") as client:
        resp = client._client.get("/points")

    assert resp.status_code == 200


# ===========================================================================
# Async client context manager
# ===========================================================================


@respx.mock
async def test_async_client_context_manager() -> None:
    """AsyncPIWebAPIClient works as an async context manager."""
    respx.get(f"{BASE}/points").mock(
        return_value=httpx.Response(200, json={"WebId": "P01", "Name": "test"})
    )

    async with AsyncPIWebAPIClient(BASE, username="user", password="pass") as client:
        assert client._client is not None
