"""Wajub SDK exceptions."""

from __future__ import annotations


class WajubError(Exception):
    """An error answered by the Wajub API, or a request that got no answer.

    ``errors`` holds the first validation message of each field;
    ``field_errors`` holds every message of each field, in the order the API
    sent them.
    """

    def __init__(
        self,
        message: str,
        code: str = "api_error",
        http_status: int | None = None,
        errors: dict[str, str | list[str]] | None = None,
        raw: dict | None = None,
        *,
        field_errors: dict[str, list[str]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.errors = errors
        self.field_errors = field_errors
        self.raw = raw


class AuthenticationError(WajubError):
    pass


class PermissionError(WajubError):
    pass


class NotFoundError(WajubError):
    pass


class InvalidRequestError(WajubError):
    pass


class RateLimitError(WajubError):
    def __init__(
        self,
        message: str,
        code: str = "rate_limit",
        http_status: int | None = 429,
        errors: dict[str, str | list[str]] | None = None,
        raw: dict | None = None,
        retry_after: int | None = None,
        *,
        field_errors: dict[str, list[str]] | None = None,
    ) -> None:
        super().__init__(message, code, http_status, errors, raw, field_errors=field_errors)
        self.retry_after = retry_after


class ApiConnectionError(WajubError):
    pass


class WebhookSignatureVerificationError(Exception):
    pass
