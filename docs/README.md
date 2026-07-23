# Overview

`cryptoix-python` is the official Python Software Development Kit (SDK) for integrating with the Cryptoix Merchant and Payment APIs. Designed for modern Python applications, the SDK abstracts low-level HTTP interactions, signature verifications, pagination, custom error mapping, and automatic rate-limit retries. It allows developers to securely manage payment gateways, merchant transactions, payouts, refunds, escrows, invoices, webhooks, and QR code endpoints.

> [!NOTE]
> You should [Refer to this Section](https://cryptoix.io/dashboard/api-keys 'Dashboard/API KEYS - Cryptoix') to obtain or create the API key required for use.

The codebase adheres to modern Python packaging standards (PEP 517/621 via Hatchling) and utilizes a standard `src/` layout with `httpx` for efficient synchronous HTTP execution.

---

## Key Features

- **Robust Client Management**: Built on top of `httpx` (`>=0.27`), supporting context management (`__enter__` / `__exit__`) for reliable resource lifecycle handling.
- **Automatic 429 Retries**: Automatically detects HTTP `429` Rate Limit responses, inspects `retry_after` duration payloads, backs off, and re-executes requests seamlessly.
- **Strict TypedDict Contracts**: Leverages Python type annotations and `TypedDict` contracts to provide clear static type checking and structural validation.
- **Secure Webhook Verification**: Implements HMAC-SHA256 signature verification utilizing constant-time comparison (`hmac.compare_digest`) to protect against timing side-channel attacks.
- **Structured Exception Hierarchy**: Maps HTTP and API-level errors cleanly to specific exceptions (`CryptoixAuthenticationError`, `CryptoixValidationError`, `CryptoixRateLimitError`) carrying request IDs and detailed error metadata.

---

## Quickstart

### Installation

Install the package directly from your local development environment or source tree using your preferred PEP 517 build frontend:

```bash
pip install .
```

### Basic Usage

To interact with the Cryptoix API, instantiate the `CryptoixClient` using Python's context manager to ensure proper cleanup of underlying transport connections. 

> **Security Best Practice**: Never hardcode API keys directly into source code. Always inject secrets securely via environment variables (such as `CRYPTOIX_API_KEY`).

```python
import os
from cryptoix import CryptoixClient, CryptoixAPIError

# Retrieve API key from environment variables
api_key = os.getenv("CRYPTOIX_API_KEY", "your_api_key_here")

try:
    # Use CryptoixClient as a context manager
    with CryptoixClient(api_key=api_key) as client:
        # Create a sample payment order
        payment_response = client.create_payment(
            amount=50.00,
            currency="USD",
            metadata={"order_id": "cart_98765"}
        )
        print("Payment Created Successfully:", payment_response)

except CryptoixAPIError as e:
    print(f"Cryptoix API Error [{e.status_code}] ({e.code}): {e.message}")
    if e.request_id:
        print(f"Request ID: {e.request_id}")
```

---

## SDK Architecture Overview

The `cryptoix-python` SDK is organized around clean separation of concerns, isolating transport logic, security primitives, and error handling across dedicated internal modules:

```
                         +-----------------------------+
                         |     Client Application      |
                         +--------------+--------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
     +-----------------------+                     +-----------------------+
     |    CryptoixClient     |                     |   webhooks module     |
     | (src/cryptoix/client) |                     |(src/cryptoix/webhooks)|
     +-----------+-----------+                     +-----------+-----------+
                 |                                             |
   +-------------+-------------+                               |
   | HTTP Requests / Auth      |                               |
   | Custom Error Mapping      |                               | HMAC-SHA256
   | Auto-retry on 429        |                               | Verification
   +-------------+-------------+                               |
                 |                                             |
                 v                                             v
     +-----------------------+                     +-----------------------+
     |     Cryptoix API      |                     | Incoming Webhook Payload
     +-----------------------+                     +-----------------------+
```

### Component Breakdown

1. **API Client (`src/cryptoix/client.py`)**: 
   - Core entry point wrapping `httpx.Client`.
   - Handles environment configuration (`DEFAULT_BASE_URL`, `DEFAULT_PUBLIC_URL`, `DEFAULT_QR_URL`), authentication header injection, and response payload unwrapping from standard `ApiEnvelope` wrappers.
2. **Exception Hierarchy (`src/cryptoix/errors.py`)**:
   - Exposes `CryptoixAPIError` alongside specialized subclasses (`CryptoixAuthenticationError`, `CryptoixValidationError`, `CryptoixRateLimitError`) to capture precise failure context.
3. **Webhook Security (`src/cryptoix/webhooks.py`)**:
   - Provides `compute_webhook_signature()` and `verify_webhook_signature()` to authenticate incoming provider notifications safely.
4. **Pagination (`src/cryptoix/pagination.py`)**:
   - A frozen dataclass managing `page` and `per_page` query parameter construction for listing endpoints.

---

## Documentation Index

Explore the rest of the codebase and technical specifications through the following resources:

- **Core Client & Methods**: Consult `src/cryptoix/client.py` for full signatures of payment creation, payout processing, refund execution, and transaction listing methods.
- **Webhook Integration Guide**: Review `src/cryptoix/webhooks.py` and `tests/test_webhooks.py` for implementation patterns on constant-time signature validation.
- **Error Handling**: Review `src/cryptoix/errors.py` to inspect exception attributes (`status_code`, `code`, `details`, `request_id`).
- **Test Suite & Mocks**: Examine `tests/test_client.py` for examples of testing client integrations using `httpx.MockTransport`.
