"""Tests for authentication helpers."""

import httpx
import pytest

from pisharp_piwebapi.auth import basic_auth, kerberos_auth, ntlm_auth


def test_basic_auth_returns_httpx_auth() -> None:
    """basic_auth returns an httpx.BasicAuth instance."""
    auth = basic_auth("user", "pass")
    assert isinstance(auth, httpx.BasicAuth)


def test_kerberos_auth_import_error() -> None:
    """Kerberos auth should raise a clear error if httpx-gssapi is not installed."""
    # This test will pass in environments without httpx-gssapi
    # and skip in environments where it is installed
    try:
        kerberos_auth()
        pytest.skip("httpx-gssapi is installed")
    except ImportError as e:
        assert "kerberos" in str(e).lower()


def test_ntlm_auth_import_error() -> None:
    """ntlm_auth raises ImportError with an actionable message if httpx-ntlm is absent."""
    try:
        ntlm_auth("DOMAIN\\user", "pass")
        pytest.skip("httpx-ntlm is installed")
    except ImportError as e:
        assert "ntlm" in str(e).lower()
        assert "pip install" in str(e)


def test_ntlm_auth_message_mentions_extra() -> None:
    """The ImportError from ntlm_auth names the correct pip extra."""
    try:
        ntlm_auth("user", "pass")
        pytest.skip("httpx-ntlm is installed")
    except ImportError as e:
        assert "pisharp-piwebapi[ntlm]" in str(e)
