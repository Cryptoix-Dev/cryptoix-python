# Troubleshooting Guide

This troubleshooting guide provides developers with instructions, code patterns, and diagnostic steps for resolving integration issues, API errors, and authentication failures when using the `cryptoix-python` SDK.

---

## Common Error Codes & Exceptions

The `cryptoix-python` SDK wraps API failure responses in a structured exception hierarchy rooted at `CryptoixAPIError`. Every instance of `CryptoixAPIError` encapsulates the underlying error properties for granular logging, debugging, and tracing:

- `status_code`: The HTTP status code returned by the API server.
- `code`: The machine-readable application error code string (e.g., `invalid_payload`, `rate_limit_exceeded`).
- `details`: A dictionary containing additional field-level or context-specific error details.
- `request_id`: The unique tracking identifier returned by the gateway for the request (crucial for support escalations).

### Exception Hierarchy

```python
from cryptoix import (
    CryptoixAPIError,
    CryptoixAuthenticationError,
    CryptoixRateLimitError,
    CryptoixValidationError,
)
```

### Example: Catching and Inspecting Exceptions

```python
from cryptoix import CryptoixClient, CryptoixAPIError

client = CryptoixClient(api_key="your_api_key_here")

try:
    payment = client.create_payment({"amount": 100.00, "currency": "USD"})
except CryptoixAPIError as e:
    print(f"API Error Occurred:")
    print(f"  HTTP Status : {e.status_code}")
    print(f"  Error Code  : {e.code}")
    print(f"  Details     : {e.details}")
    print(f"  Request ID  : {e.request_id}")
```

---

## Authentication & Authorization Failures (HTTP 401/403)

HTTP status codes `401 Unauthorized` and `403 Forbidden` indicate problems with your API credentials or authorization permissions.

### Diagnosing Missing or Invalid API Keys

1. **Verify Client Initialization**: Ensure you are passing a valid API key into `CryptoixClient`, or that the environment variable `CRYPTOIX_API_KEY` is correctly set in your execution environment.
   ```python
   import os
   from cryptoix import CryptoixClient

   # The client will automatically fall back to CRYPTOIX_API_KEY if omitted
   client = CryptoixClient()
   ```
2. **Check for Source Control Leaks**: Never hardcode API keys directly in source files. If an API key is accidentally committed to source control, immediately revoke and regenerate it via your Cryptoix dashboard.
3. **Inspect the Token Scope**: A `403 Forbidden` error typically means the API key is authenticated but lacks permissions to execute the requested endpoint (e.g., attempting a payout action with a restricted merchant key).

---

## Handling Rate Limits (HTTP 429)

When your application exceeds its assigned request quota, the API returns an HTTP `429 Too Many Requests` status code. 

### Built-in Handling & Custom Timeouts
- The `CryptoixClient` (`src/cryptoix/client.py`) includes automatic retry logic for HTTP `429` responses based on the `retry_after` duration payload returned by the gateway.
- If your application encounters persistent rate limiting that exceeds automatic threshold configurations, wrap your calls with custom backoff handlers or adjust request pacing.

### Example: Handling Rate Limit Exceptions Explicitly

```python
import time
from cryptoix import CryptoixClient, CryptoixRateLimitError

client = CryptoixClient()

try:
    transactions = client.list_transactions(pagination={"page": 1, "per_page": 50})
except CryptoixRateLimitError as e:
    retry_seconds = e.details.get("retry_after", 5)
    print(f"Rate limit hit. Retrying after {retry_seconds} seconds (Request ID: {e.request_id}).")
    time.sleep(retry_seconds)
    # Retry your operation safely here
```

---

## Payload Validation Errors (HTTP 422)

An HTTP `422 Unprocessable Entity` response triggers a `CryptoixValidationError`. This occurs when the request payload fails structural validation, contains missing required fields, or supplies invalid data types.

### Example: Inspecting Field Validation Failures

```python
from cryptoix import CryptoixClient, CryptoixValidationError

client = CryptoixClient()

try:
    client.create_payment({"amount": "invalid_amount"})
except CryptoixValidationError as e:
    print(f"Validation failed (Request ID: {e.request_id})")
    for field, error_message in e.details.items():
        print(f"  - Field '{field}': {error_message}")
```

---

## Inspecting Request & Response Envelopes

The `cryptoix-python` SDK communicates with the Cryptoix API by parsing responses from a standardized envelope format (`ApiEnvelope`, defined in `src/cryptoix/types.py`).

- Successful responses automatically unwrap structural metadata (`ApiMeta`) and return clean response data objects to the caller.
- When debugging unexpected responses, ensure your development or test environments point to the correct base URLs (`DEFAULT_BASE_URL`, `DEFAULT_PUBLIC_URL`, or `DEFAULT_QR_URL` in `src/cryptoix/client.py`).

---

## Secure Webhook Signature Verification

When handling incoming webhook notifications from Cryptoix, always verify the webhook signature using `verify_webhook_signature` from `src/cryptoix/webhooks.py`. This function uses `hmac.compare_digest` to perform constant-time comparisons, preventing timing attacks.

### Example: Secure Webhook Verification in an Application

```python
from cryptoix import verify_webhook_signature

webhook_secret = "your_webhook_secret_key"
raw_payload_bytes = b'{"event":"payment.completed","id":"pay_123"}'
received_signature = "sha256=abcdef..."

is_valid = verify_webhook_signature(
    payload=raw_payload_bytes,
    signature=received_signature,
    secret=webhook_secret,
)

if not is_valid:
    raise ValueError("Invalid webhook signature! Request rejected.")
```
