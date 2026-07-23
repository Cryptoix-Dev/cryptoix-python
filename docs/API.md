---
title: API
slug: api
lang: en
project: Cryptoix-python
domain: https://github.com/Cryptoix-Dev/cryptoix-python
---
## API Documentation

Welcome to the technical documentation and code reference for `cryptoix-python`, the official Python SDK for integrating with the Cryptoix Merchant and Payment APIs. 

This reference details the core SDK classes, full method signatures, exception hierarchy, webhook utilities, pagination models, and static type definitions.

---

### Package Entry Point & Imports

All public components are exposed directly from the package root. You can import classes, functions, and exceptions from `cryptoix`:

```python
from cryptoix import (
    CryptoixClient,
    CryptoixAPIError,
    CryptoixAuthenticationError,
    CryptoixRateLimitError,
    CryptoixValidationError,
    verify_webhook_signature,
    compute_webhook_signature,
)
```

---

### Client API (`CryptoixClient`)

**Source File:** `src/cryptoix/client.py`

The `CryptoixClient` class is the main SDK entrypoint, implemented as a wrapper over `httpx.Client`. It manages API key authentication headers, URL formatting across base endpoints (`DEFAULT_BASE_URL`, `DEFAULT_PUBLIC_URL`, `DEFAULT_QR_URL`), automatic retries on rate limits (`429`), and the unwrapping of standard `ApiEnvelope` payloads.

`CryptoixClient` supports context management (`__enter__` / `__exit__`) to ensure underlying HTTP connections are cleaned up correctly.

#### Security Best Practice: API Keys
Never hardcode API keys or commit them to source control. Load your API key from secure storage or the environment variable `CRYPTOIX_API_KEY`:

```python
import os
from cryptoix import CryptoixClient

# The client automatically falls back to OS environment variables if api_key is omitted
client = CryptoixClient(api_key=os.environ.get("CRYPTOIX_API_KEY"))
```

#### Client Initialization & Context Management

```python
with CryptoixClient(api_key="sec_live_...") as client:
    payment = client.create_payment(
        amount=100.00,
        currency="USD",
        metadata={"order_id": "ord_98765"}
    )
```

#### Full Method Signatures and Parameters

##### Constructor
* `__init__(api_key: str | None = None, base_url: str | None = None, timeout: float = 30.0) -> None`
  Initializes the API client. If `api_key` is `None`, the client checks the `CRYPTOIX_API_KEY` environment variable.

##### Payments
* `create_payment(amount: float, currency: str, **kwargs) -> JsonDict`
  Initiates a new payment order on the gateway.
  - **Parameters:**
    - `amount` (`float`): The monetary value of the payment.
    - `currency` (`str`): The 3-letter currency code (e.g., `"USD"`, `"EUR"`).
    - `**kwargs`: Additional optional parameters such as `metadata`, `customer_id`, or `callback_url`.

##### Transactions
* `list_transactions(pagination: Pagination | None = None, **kwargs) -> JsonDict`
  Retrieves merchant transaction history.
  - **Parameters:**
    - `pagination` (`Pagination | None`): Optional pagination instance specifying `page` and `per_page`.
    - `**kwargs`: Additional filter parameters like status or date ranges.

##### Payouts & Refunds
* `create_payout(amount: float, currency: str, destination: str, **kwargs) -> JsonDict`
  Disburses merchant funds to an external destination.
  - **Parameters:**
    - `amount` (`float`): The payout amount.
    - `currency` (`str`): Currency code.
    - `destination` (`str`): Destination wallet address or bank reference identifier.
    - `**kwargs`: Additional metadata or routing configuration.

* `create_refund(transaction_id: str, amount: float | None = None, **kwargs) -> JsonDict`
  Issues a full or partial refund for a completed transaction.
  - **Parameters:**
    - `transaction_id` (`str`): The original transaction identifier.
    - `amount` (`float | None`): Optional partial refund amount. If omitted, full transaction amount is refunded.
    - `**kwargs`: Additional options like reason codes.

##### Escrows & Invoices
* `create_escrow(amount: float, currency: str, terms: JsonDict, **kwargs) -> JsonDict`
  Establishes a new escrow arrangement holding funds securely.
  - **Parameters:**
    - `amount` (`float`): Escrow value.
    - `currency` (`str`): Currency code.
    - `terms` (`JsonDict`): Dictionary defining escrow release conditions.
    - `**kwargs`: Additional metadata.

* `create_invoice(amount: float, currency: str, due_date: str, **kwargs) -> JsonDict`
  Generates a formal invoice for customer payment.
  - **Parameters:**
    - `amount` (`float`): Invoice amount.
    - `currency` (`str`): Currency code.
    - `due_date` (`str`): ISO-8601 formatted expiration date string.
    - `**kwargs`: Line items and client details.

##### Webhooks & QR Codes
* `configure_webhook(url: str, events: list[str], **kwargs) -> JsonDict`
  Registers or updates a merchant webhook destination endpoint.
  - **Parameters:**
    - `url` (`str`): The public HTTPS callback endpoint URL.
    - `events` (`list[str]`): List of event identifiers to subscribe to (e.g., `["payment.success", "payout.failed"]`).
    - `**kwargs`: Additional endpoint configurations.

* `generate_qr_code(amount: float, currency: str, **kwargs) -> JsonDict`
  Generates a dynamic payment QR code payload.
  - **Parameters:**
    - `amount` (`float`): Payment amount represented in the QR code.
    - `currency` (`str`): Currency code.
    - `**kwargs`: Size specifications or format parameters.

---

### Webhook Utilities

**Source File:** `src/cryptoix/webhooks.py`

Webhook utilities provide HMAC-SHA256 signature calculations and verification functions to securely process incoming webhook notifications from Cryptoix.

#### Security Best Practice: Constant-Time Comparison
When verifying webhook signatures, always use constant-time comparisons (`hmac.compare_digest`) to prevent timing side-channel attacks. The SDK's `verify_webhook_signature` function handles this automatically.

#### Functions

* `compute_webhook_signature(payload: bytes | str, secret: str) -> str`
  Computes an HMAC-SHA256 hex digest for the given payload using the provided secret.

* `verify_webhook_signature(payload: bytes | str, signature: str, secret: str) -> bool`
  Verifies an incoming webhook signature against the computed digest in constant time.

#### Example Usage

```python
from cryptoix import verify_webhook_signature

webhook_secret = "whsec_..."
payload_bytes = request.body
incoming_signature = request.headers.get("X-Cryptoix-Signature", "")

if not verify_webhook_signature(payload_bytes, incoming_signature, webhook_secret):
    raise ValueError("Invalid webhook signature")
```

---

### Pagination Models (`Pagination`)

**Source File:** `src/cryptoix/pagination.py`

The `Pagination` model is a frozen dataclass designed to standardise list queries across endpoints like transaction histories.

#### Class Reference

```python
@dataclass(frozen=True)
class Pagination:
    page: int = 1
    per_page: int = 20

    def to_params(self) -> dict[str, int]:
        """Convert pagination model into query parameter dictionary."""
        return {
            "page": self.page,
            "per_page": self.per_page,
        }
```

#### Example Usage

```python
from cryptoix import CryptoixClient
from cryptoix.pagination import Pagination

with CryptoixClient() as client:
    page_spec = Pagination(page=2, per_page=50)
    transactions = client.list_transactions(pagination=page_spec)
```

---

### Exception Hierarchy (`CryptoixAPIError`)

**Source File:** `src/cryptoix/errors.py`

All SDK errors inherit from a common base exception (`CryptoixAPIError`), ensuring predictable exception handling across integration code.

```
CryptoixAPIError
├── CryptoixAuthenticationError (HTTP 401 / 403)
├── CryptoixValidationError     (HTTP 422)
└── CryptoixRateLimitError      (HTTP 429)
```

#### Base Exception: `CryptoixAPIError`
Stores detailed diagnostic data returned by the API gateway:
* `status_code`: HTTP status code returned by the server.
* `code`: Machine-readable error code string.
* `details`: Dictionary or string containing validation or error details.
* `request_id`: Unique tracking ID for the HTTP request.

#### Derived Exceptions

* **`CryptoixAuthenticationError`**: Raised when requests fail authentication or authorisation checks (HTTP `401` or `403`).
* **`CryptoixValidationError`**: Raised when request payloads or parameters fail server-side validation (HTTP `422`).
* **`CryptoixRateLimitError`**: Raised when rate limits are exceeded (HTTP `429`). Exposes a `retry_after` attribute indicating how long to wait before subsequent requests.

#### Exception Handling Example

```python
from cryptoix import CryptoixClient, CryptoixRateLimitError, CryptoixAPIError
import time

client = CryptoixClient()

try:
    client.create_payment(amount=50.0, currency="EUR")
except CryptoixRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds.")
    time.sleep(e.retry_after)
except CryptoixAPIError as e:
    print(f"API Error [{e.status_code}] {e.code}: {e.details} (Request ID: {e.request_id})")
```

---

### Type Definitions (`types.py`)

**Source File:** `src/cryptoix/types.py`

The SDK provides static type definitions and `TypedDict` contracts to support type checkers (such as `mypy`) and IDE autocompletion.

#### Contracts & Envelopes

* **`AuthMode`**: Type hint representing valid authentication modes or credential configurations.
* **`JsonDict`**: Shortcut type alias for `dict[str, Any]` representing JSON-serializable payloads.
* **`RequestOptions`**: Typed dictionary representing optional request configuration parameters (such as custom headers or timeouts).
* **`ApiErrorPayload`**: Structured error shape contained within error responses:
  ```python
  class ApiErrorPayload(TypedDict):
      code: str
      message: str
      details: NotRequired[JsonDict | str]
  ```
* **`ApiMeta`**: Metadata envelope accompanying standard responses:
  ```python
  class ApiMeta(TypedDict):
      request_id: str
      timestamp: int
  ```
* **`ApiEnvelope`**: Standard wrapper structure for API responses:
  ```python
  class ApiEnvelope(TypedDict):
      success: bool
      data: NotRequired[Any]
      meta: ApiMeta
      error: NotRequired[ApiErrorPayload]
  ```
