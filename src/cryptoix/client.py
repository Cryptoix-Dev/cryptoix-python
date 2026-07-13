from __future__ import annotations

import time
from typing import Any, Dict, Iterable, Optional
from urllib.parse import quote

import httpx

from .errors import (
    CryptoixAPIError,
    CryptoixAuthenticationError,
    CryptoixRateLimitError,
    CryptoixValidationError,
)

DEFAULT_BASE_URL = "https://api.cryptoix.io/v1"
DEFAULT_PUBLIC_URL = "https://cryptoix.io"
DEFAULT_QR_URL = "https://qr.cryptoix.io"


class CryptoixClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        public_url: str = DEFAULT_PUBLIC_URL,
        qr_url: str = DEFAULT_QR_URL,
        timeout: float = 30.0,
        auth_header: str = "bearer",
        max_retries: int = 1,
        client: Optional[httpx.Client] = None,
        declared_scopes: Optional[Iterable[str]] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.public_url = public_url.rstrip("/")
        self.qr_url = qr_url.rstrip("/")
        self.timeout = timeout
        self.auth_header = auth_header
        self.max_retries = max_retries
        self.declared_scopes = set(declared_scopes or [])
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "CryptoixClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _headers(self, extra: Optional[Dict[str, str]] = None, auth: bool = True) -> Dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "cryptoix-python/0.1.0"}
        if auth:
            if not self.api_key:
                raise CryptoixAuthenticationError("API key is required for this request", code="missing_api_key")
            if self.auth_header == "x-api-key":
                headers["X-API-Key"] = self.api_key
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"
        if extra:
            headers.update(extra)
        return headers

    def _url(self, path: str) -> str:
        return self.base_url + "/" + path.lstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        auth: bool = True,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        if "api_key" in clean_params:
            raise ValueError("Do not send API keys in query parameters; use headers only.")
        for attempt in range(self.max_retries + 1):
            response = self._client.request(
                method,
                self._url(path),
                json=json,
                params=clean_params,
                headers=self._headers(headers, auth=auth),
            )
            if response.status_code == 429 and attempt < self.max_retries:
                retry_after = int(response.headers.get("Retry-After", "1") or "1")
                time.sleep(min(retry_after, 5))
                continue
            return self._handle_response(response)
        raise RuntimeError("unreachable")

    def _handle_response(self, response: httpx.Response) -> Any:
        request_id = response.headers.get("X-Request-Id")
        try:
            payload = response.json()
        except ValueError:
            if response.is_error:
                raise CryptoixAPIError(
                    response.text or "HTTP error",
                    status_code=response.status_code,
                    request_id=request_id,
                    response=response,
                )
            return response.text

        if isinstance(payload, dict):
            if payload.get("ok") is False:
                err = payload.get("error") or {}
                self._raise_error(response, err, request_id)
            if payload.get("success") is False:
                self._raise_error(response, {"message": payload.get("error", "API error")}, request_id)
            if response.is_error:
                self._raise_error(response, payload.get("error", payload), request_id)
            if payload.get("ok") is True:
                return payload.get("data")
            if payload.get("success") is True:
                return payload.get("data")
        if response.is_error:
            self._raise_error(response, {}, request_id)
        return payload

    def _raise_error(self, response: httpx.Response, err: Dict[str, Any], request_id: Optional[str]) -> None:
        code = err.get("code") if isinstance(err, dict) else None
        message = err.get("message") if isinstance(err, dict) else None
        details = err.get("details") if isinstance(err, dict) else {}
        request_id = (err.get("request_id") if isinstance(err, dict) else None) or request_id
        cls = CryptoixAPIError
        if response.status_code in (401, 403):
            cls = CryptoixAuthenticationError
        if response.status_code == 429:
            raise CryptoixRateLimitError(
                message or "Rate limit exceeded",
                status_code=response.status_code,
                code=code or "rate_limited",
                details=details if isinstance(details, dict) else {},
                request_id=request_id,
                retry_after=int(response.headers.get("Retry-After", "0") or 0),
                response=response,
            )
        if response.status_code == 422:
            cls = CryptoixValidationError
        raise cls(
            message or "Cryptoix API error",
            status_code=response.status_code,
            code=code,
            details=details if isinstance(details, dict) else {},
            request_id=request_id,
            response=response,
        )

    # Legacy/public payment helpers
    def list_currencies(self) -> Any:
        return self._request("GET", "/currencies", auth=False)

    def list_rates(self) -> Any:
        return self._request("GET", "/rates")

    def create_payment(self, data: Dict[str, Any]) -> Any:
        return self._request("POST", "/payment/create", json=data)

    def check_payment(self, uuid: str) -> Any:
        return self._request("GET", f"/payment/{quote(uuid)}/check")

    def checkout_status(self, uuid: str) -> Any:
        url = f"{self.public_url}/pay/{quote(uuid)}/status"
        response = self._client.get(url, headers={"Accept": "application/json"})
        return self._handle_response(response)

    # Merchant API v1
    def list_transactions(self, **params: Any) -> Any:
        return self._request("GET", "/transactions", params=params)

    def get_transaction(self, uuid: str) -> Any:
        return self._request("GET", f"/transactions/{quote(uuid)}")

    def list_balances(self) -> Any:
        return self._request("GET", "/balances")

    def list_withdrawals(self, **params: Any) -> Any:
        return self._request("GET", "/withdrawals", params=params)

    def create_withdrawal(self, data: Dict[str, Any]) -> Any:
        return self._request("POST", "/withdrawals", json=data)

    def get_withdrawal(self, uuid: str) -> Any:
        return self._request("GET", f"/withdrawals/{quote(uuid)}")

    def list_refunds(self, **params: Any) -> Any:
        return self._request("GET", "/refunds", params=params)

    def create_refund(self, data: Dict[str, Any]) -> Any:
        return self._request("POST", "/refunds", json=data)

    def get_refund(self, uuid: str) -> Any:
        return self._request("GET", f"/refunds/{quote(uuid)}")

    def list_payouts(self, **params: Any) -> Any:
        return self._request("GET", "/payouts", params=params)

    def create_payout(self, data: Dict[str, Any]) -> Any:
        return self._request("POST", "/payouts", json=data)

    def get_payout(self, uuid: str) -> Any:
        return self._request("GET", f"/payouts/{quote(uuid)}")

    def submit_payout(self, uuid: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", f"/payouts/{quote(uuid)}/submit", json=data or {})

    def cancel_payout(self, uuid: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", f"/payouts/{quote(uuid)}/cancel", json=data or {})

    def list_payment_links(self, **params: Any) -> Any:
        return self._request("GET", "/payment-links", params=params)

    def create_payment_link(self, data: Dict[str, Any]) -> Any:
        return self._request("POST", "/payment-links", json=data)

    def list_invoices(self, **params: Any) -> Any:
        return self._request("GET", "/invoices", params=params)

    def create_invoice(self, data: Dict[str, Any]) -> Any:
        return self._request("POST", "/invoices", json=data)

    def get_invoice(self, uuid: str) -> Any:
        return self._request("GET", f"/invoices/{quote(uuid)}")

    def send_invoice(self, uuid: str) -> Any:
        return self._request("POST", f"/invoices/{quote(uuid)}/send")

    def list_escrows(self, **params: Any) -> Any:
        return self._request("GET", "/escrows", params=params)

    def create_escrow(self, data: Dict[str, Any]) -> Any:
        return self._request("POST", "/escrows", json=data)

    def get_escrow(self, uuid: str) -> Any:
        return self._request("GET", f"/escrows/{quote(uuid)}")

    def fund_escrow(self, uuid: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", f"/escrows/{quote(uuid)}/fund", json=data or {})

    def request_escrow_release(self, uuid: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", f"/escrows/{quote(uuid)}/request-release", json=data or {})

    def dispute_escrow(self, uuid: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", f"/escrows/{quote(uuid)}/dispute", json=data or {})

    def list_webhook_deliveries(self, **params: Any) -> Any:
        return self._request("GET", "/webhook-deliveries", params=params)

    def replay_webhook_delivery(self, delivery_id: int) -> Any:
        return self._request("POST", f"/webhook-deliveries/{delivery_id}/replay")

    def qr_url_for(self, data: str, **params: Any) -> str:
        from urllib.parse import urlencode
        query = {"data": data, **{k: v for k, v in params.items() if v is not None}}
        return f"{self.qr_url}/v1/create/qr?{urlencode(query)}"

    def qr_health(self) -> Any:
        response = self._client.get(f"{self.qr_url}/health", headers={"Accept": "application/json"})
        return self._handle_response(response)
