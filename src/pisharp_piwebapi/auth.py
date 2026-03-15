"""Authentication helpers for PI Web API."""

from __future__ import annotations

import httpx


def basic_auth(username: str, password: str) -> httpx.BasicAuth:
    """Create Basic authentication for PI Web API.

    Args:
        username: PI Web API username (e.g., "domain\\user" or "user").
        password: PI Web API password.

    Returns:
        httpx.BasicAuth instance to pass to the client.
    """
    return httpx.BasicAuth(username=username, password=password)


def kerberos_auth() -> httpx.Auth:
    """Create Kerberos (Windows Integrated) authentication.

    Requires the `kerberos` extra: `pip install pisharp-piwebapi[kerberos]`

    Returns:
        Kerberos auth instance for httpx.

    Raises:
        ImportError: If httpx-gssapi is not installed.
    """
    try:
        from httpx_gssapi import HTTPSPNEGOAuth  # type: ignore[import-untyped]
    except ImportError:
        raise ImportError(
            "Kerberos auth requires the 'kerberos' extra. "
            "Install with: pip install pisharp-piwebapi[kerberos]"
        ) from None
    return HTTPSPNEGOAuth()  # type: ignore[return-value]
