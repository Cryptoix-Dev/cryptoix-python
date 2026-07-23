---
title: CONFIGURATION
slug: configuration
lang: en
project: Cryptoix-python
domain: https://github.com/Cryptoix-Dev/cryptoix-python
generated_by: agenter
---
## Configuration & Environment

This document outlines configuration options, environment variables, endpoint overrides, and automated resilience mechanisms for the `cryptoix-python` SDK.

---

### Environment Variables

The SDK checks the system environment for default configuration values when explicit arguments are omitted during client initialization.

* **`CRYPTOIX_API_KEY`**: The primary credential used for authenticating requests against Cryptoix Merchant and Payment APIs.
  
#### Security Best Practices
- **Never hardcode API keys** directly in source code or check them into version control systems.
- Use secure environment variable injection, `.env` files protected by local file permissions (and excluded via `.gitignore`), or secret managers (e.g., AWS Secrets Manager, HashiCorp Vault).
- When validating incoming webhooks, always use `verify_webhook_signature()` from `cryptoix.webhooks`, which utilizes `hmac.compare_digest` under the hood to perform **constant-time comparisons** and prevent timing side-channel attacks.

---

### Client Configuration Options

When instantiating `CryptoixClient` directly in your Python code, you can pass explicit options to configure authentication and target endpoints.

```python
from cryptoix import CryptoixClient

client = CryptoixClient(
    api_key="your_api_key_here",
    base_url="https://api.cryptoix.com/v1",       # Optional override
    public_url="https://public.cryptoix.com/v1",   # Optional override
    qr_url="https://qr.cryptoix.com/v1",           # Optional override
)
```

If `api_key` is omitted during initialization, the SDK automatically attempts to read the `CRYPTOIX_API_KEY` environment variable.

---

### Custom Base URLs & Environments

For staging environments, sandbox testing, or localized development proxies, you can override the SDK's default base URLs. These defaults are defined in `src/cryptoix/client.py`:

* `DEFAULT_BASE_URL`: Base URL for core merchant API endpoints.
* `DEFAULT_PUBLIC_URL`: Base URL for public API endpoints.
* `DEFAULT_QR_URL`: Base URL for payment QR code generation.

#### Example: Configuring for a Sandbox Environment

```python
from cryptoix import CryptoixClient

sandbox_client = CryptoixClient(
    api_key="sandbox_api_key_abc123",
    base_url="https://sandbox-api.cryptoix.com/v1",
    public_url="https://sandbox-public.cryptoix.com/v1",
    qr_url="https://sandbox-qr.cryptoix.com/v1",
)
```

Using Python's context manager support ensures underlying `httpx` transport resources are cleaned up safely:

```python
with CryptoixClient(api_key="sandbox_api_key_abc123") as client:
    payment = client.create_payment(amount=100.0, currency="USDT")
```

---

### Retry & Rate Limit Behavior

The `CryptoixClient` handles transient rate-limiting errors automatically to maintain application resilience.

#### HTTP 429 Rate Limit Handling
When the Cryptoix API returns an HTTP `429 Too Many Requests` status code, the SDK performs the following steps:
1. **Catches** the rate limit response mapped via `CryptoixRateLimitError`.
2. **Extracts** the duration specified by the server's rate limit or retry header (`retry_after`).
3. **Pauses** execution using an automated `time.sleep()` backoff for the designated duration.
4. **Retries** the request transparently.

#### Handling Unrecoverable Errors
If rate limits persist beyond maximum retry thresholds or if other API errors occur, the SDK raises specific exceptions defined in `src/cryptoix/errors.py`:

* **`CryptoixAPIError`**: Base exception storing `status_code`, error `code`, `details`, and `request_id`.
* **`CryptoixAuthenticationError`**: Raised on HTTP `401` or `403` authorization failures.
* **`CryptoixValidationError`**: Raised on invalid input payloads or HTTP `422` responses.
* **`CryptoixRateLimitError`**: Exposes rate limit details including the associated `retry_after` payload value.

```python
from cryptoix import CryptoixClient, CryptoixRateLimitError, CryptoixAPIError

client = CryptoixClient()

try:
    transactions = client.list_transactions(page=1, per_page=10)
except CryptoixRateLimitError as e:
    print(f"Rate limited. Please retry after {e.retry_after} seconds.")
except CryptoixAPIError as e:
    print(f"API Error [{e.status_code}] {e.code}: {e.details} (Request ID: {e.request_id})")
```
