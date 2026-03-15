"""Custom exceptions for the PI Web API SDK."""

from __future__ import annotations

from typing import Any


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
