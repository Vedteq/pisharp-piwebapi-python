"""Tests for authentication helpers."""

import httpx
import pytest

from pisharp_piwebapi.auth import basic_auth, kerberos_auth


def test_basic_auth_returns_httpx_auth():
    auth = basic_auth("user", "pass")
    assert isinstance(auth, httpx.BasicAuth)


def test_kerberos_auth_import_error():
    """Kerberos auth should raise a clear error if httpx-gssapi is not installed."""
    # This test will pass in environments without httpx-gssapi
    # and skip in environments where it is installed
    try:
        kerberos_auth()
        pytest.skip("httpx-gssapi is installed")
    except ImportError as e:
        assert "kerberos" in str(e).lower()
