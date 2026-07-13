from __future__ import annotations

from typing import Any, Mapping, Optional


class CryptoixAPIError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        details: Optional[Mapping[str, Any]] = None,
        request_id: Optional[str] = None,
        response: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = dict(details or {})
        self.request_id = request_id
        self.response = response


class CryptoixAuthenticationError(CryptoixAPIError):
    pass


class CryptoixRateLimitError(CryptoixAPIError):
    def __init__(self, *args: Any, retry_after: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after = retry_after


class CryptoixValidationError(CryptoixAPIError):
    pass
