"""Tests for authentication helpers."""

import httpx
import pytest

from pisharp_piwebapi.auth import _RedactedAuth, basic_auth, kerberos_auth, ntlm_auth


def test_basic_auth_returns_redacted_wrapper() -> None:
    """basic_auth returns a _RedactedAuth wrapping httpx.BasicAuth."""
    auth = basic_auth("user", "pass")
    assert isinstance(auth, _RedactedAuth)
    assert isinstance(auth, httpx.Auth)


def test_basic_auth_repr_hides_credentials() -> None:
    """basic_auth repr does not leak username or password."""
    auth = basic_auth("admin", "s3cret!")
    r = repr(auth)
    assert "s3cret!" not in r
    assert "admin" not in r
    assert "BasicAuth" in r
    assert "redacted" in r.lower()


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


def test_ntlm_auth_returns_redacted_wrapper() -> None:
    """ntlm_auth wraps the auth object so repr does not leak credentials."""
    try:
        auth = ntlm_auth("DOMAIN\\user", "s3cret!")
    except ImportError:
        pytest.skip("httpx-ntlm is not installed")
    assert isinstance(auth, _RedactedAuth)
    r = repr(auth)
    assert "s3cret!" not in r
    assert "redacted" in r.lower()


def test_redacted_auth_repr_hides_credentials() -> None:
    """_RedactedAuth repr never leaks the inner object's repr."""
    inner = basic_auth("admin", "p@ssword")
    wrapped = _RedactedAuth(inner, label="TestAuth")
    r = repr(wrapped)
    assert r == "TestAuth(credentials=<redacted>)"
    assert "p@ssword" not in r
