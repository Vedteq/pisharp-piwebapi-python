"""Custom exceptions for the PI Web API SDK."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import httpx

# PI Web API WebIDs are Base64url-encoded opaque tokens.
_WEB_ID_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


def validate_web_id(value: str, param_name: str = "web_id") -> None:
    """Raise ``ValueError`` if *value* is not a valid PI Web API WebID.

    Called at the top of every resource method that embeds a WebID (or
    similar identifier like a marker) into a URL path segment.  Validates
    that the value is non-empty and contains only Base64url-safe characters
    (``[A-Za-z0-9_-]``), which prevents path traversal and injection attacks.

    Args:
        value: The WebID or identifier string to validate.
        param_name: Name of the parameter (used in the error message).

    Raises:
        ValueError: If *value* is empty, whitespace-only, or contains
            characters outside the Base64url alphabet.
    """
    if not value or not value.strip():
        raise ValueError(
            f"{param_name} must not be empty. "
            "Pass a valid PI Web API WebID string."
        )
    if not _WEB_ID_RE.match(value):
        raise ValueError(
            f"{param_name} contains invalid characters. "
            "A WebID must consist only of alphanumeric characters, "
            "hyphens, and underscores."
        )


class PIWebAPIError(Exception):
    """Base exception for all PI Web API errors."""

    def __init__(self, message: str, status_code: int | None = None, body: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class AuthenticationError(PIWebAPIError):
    """Raised when authentication fails (401/403)."""


class NotFoundError(PIWebAPIError):
    """Raised when a resource is not found (404)."""


class BatchError(PIWebAPIError):
    """Raised when a batch request contains partial failures."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class RateLimitError(PIWebAPIError):
    """Raised when the API rate limit is exceeded (429)."""


class ServerError(PIWebAPIError):
    """Raised when the server returns a 5xx error."""


# ---------------------------------------------------------------------------
# Shared error-classification helpers used by both the event hooks and the
# resource mixin methods.
# ---------------------------------------------------------------------------


def classify_error(status: int, message: str, body: Any) -> PIWebAPIError:
    """Map an HTTP status code to the most-specific SDK exception.

    Args:
        status: The HTTP response status code.
        message: Human-readable error message (extracted from the body if possible).
        body: Parsed response body — either a ``dict`` from JSON or a raw string.

    Returns:
        An instance of the appropriate :class:`PIWebAPIError` subclass.
    """
    if status in (401, 403):
        return AuthenticationError(message, status_code=status, body=body)
    if status == 404:
        return NotFoundError(message, status_code=status, body=body)
    if status == 429:
        return RateLimitError(message, status_code=status, body=body)
    if status >= 500:
        return ServerError(message, status_code=status, body=body)
    return PIWebAPIError(message, status_code=status, body=body)


def raise_for_response(response: httpx.Response) -> None:
    """Raise the appropriate SDK exception for a non-2xx response.

    This is the sync counterpart used directly in mixin methods.  The async
    path uses :func:`raise_for_response_async`.  Both functions are no-ops on
    successful (2xx) responses.

    Args:
        response: A fully-read :class:`httpx.Response`.

    Raises:
        AuthenticationError: On 401 or 403.
        NotFoundError: On 404.
        RateLimitError: On 429.
        ServerError: On 5xx.
        PIWebAPIError: On any other non-2xx status.
    """
    if response.is_success:
        return

    status = response.status_code
    try:
        body = response.json()
    except Exception:
        body = response.text

    message = f"PI Web API error {status}"
    if isinstance(body, dict) and "Message" in body:
        message = body["Message"]

    raise classify_error(status, message, body)


async def raise_for_response_async(response: httpx.Response) -> None:
    """Raise the appropriate SDK exception for a non-2xx response (async).

    Ensures the response body is read before inspecting it so callers do not
    need to call ``await response.aread()`` themselves.

    Args:
        response: An :class:`httpx.Response` from an async request.

    Raises:
        AuthenticationError: On 401 or 403.
        NotFoundError: On 404.
        RateLimitError: On 429.
        ServerError: On 5xx.
        PIWebAPIError: On any other non-2xx status.
    """
    if response.is_success:
        return

    await response.aread()
    status = response.status_code
    try:
        body = response.json()
    except Exception:
        body = response.text

    message = f"PI Web API error {status}"
    if isinstance(body, dict) and "Message" in body:
        message = body["Message"]

    raise classify_error(status, message, body)
