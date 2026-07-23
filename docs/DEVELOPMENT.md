# Developer Documentation: `cryptoix-python`

Welcome to the contributor and developer documentation for `cryptoix-python`, the official Python Software Development Kit (SDK) for integrating with the Cryptoix Merchant and Payment APIs. This document outlines the project structure, build system, test procedures, HTTP transport mocking strategies, and code quality standards required for maintaining and contributing to the SDK.

---

## Project Structure

`cryptoix-python` follows a modern Python standard `src/` layout. This isolates production source code from root-level configuration files and test artifacts, ensuring that tests are always run against an installed or correctly path-resolved version of the package.

```
cryptoix-python/
├── pyproject.toml             # PEP 517 / PEP 621 configuration & dependencies
├── src/
│   └── cryptoix/              # Package root
│       ├── __init__.py        # Public API exposure (__all__)
│       ├── client.py          # CryptoixClient wrapper & HTTP execution
│       ├── errors.py          # Custom exception hierarchy
│       ├── pagination.py      # Frozen dataclass for pagination state
│       ├── types.py           # Static typing definitions & TypedDict contracts
│       └── webhooks.py        # HMAC-SHA256 signature verification
├── tests/
│   ├── test_client.py         # Client integration & MockTransport tests
│   └── test_webhooks.py       # Webhook cryptographic verification tests
└── examples/
    ├── create_payment.py      # Runnable payment generation script
    ├── list_transactions.py   # Runnable transaction listing with pagination
    └── verify_webhook.py      # Runnable webhook validation example
```

---

## Build System (Hatchling / PEP 517)

The project uses **Hatchling** (`>=1.25`) as its PEP 517 build backend. All package metadata, build targets, and dependencies are declared natively within `pyproject.toml`. Legacy `setup.py` or `setup.cfg` tooling is intentionally omitted.

To set up your local development environment, clone the repository and install the package in editable mode along with its development and testing dependencies:

```bash
# Clone the repository
git clone https://github.com/Cryptoix-Dev/cryptoix-python.git
cd cryptoix-python

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in editable mode with development dependencies
pip install --upgrade pip
pip install -e ".[dev]"
```

---

## Running Unit Tests

The test suite is built on top of `pytest`. Because the package uses a `src/` layout, running `pytest` directly will automatically discover and execute tests against the source code isolation layer.

To execute the test suite:

```bash
pytest
```

To run tests with verbose output or targeted execution:

```bash
# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_client.py
```

---

## Mocking HTTP Transports with `httpx.MockTransport`

To prevent SDK tests from making live network calls to the Cryptoix API, `cryptoix-python` leverages `httpx.MockTransport`. This allows developers to intercept HTTP requests synchronously, inspect outgoing headers, payloads, and authentication tokens, and return deterministic mock responses.

### Example: Testing Client Requests and Error Mappings

The following example demonstrates how `tests/test_client.py` uses `httpx.MockTransport` to test successful envelope unwrapping and error handling without hitting real endpoints:

```python
import httpx
import pytest
from cryptoix import CryptoixClient, CryptoixAPIError

def test_client_payment_creation() -> None:
    # Define a custom handler to intercept requests
    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/payments"
        assert request.headers.get("Authorization") == "Bearer test_api_key"
        
        # Return a simulated success response matching the ApiEnvelope structure
        return httpx.Response(
            status_code=200,
            json={
                "meta": {"request_id": "req_12345"},
                "data": {"payment_id": "pay_98765", "status": "pending"}
            }
        )

    # Instantiate the client using MockTransport
    transport = httpx.MockTransport(mock_handler)
    with CryptoixClient(api_key="test_api_key", transport=transport) as client:
        result = client.create_payment({"amount": 100.00, "currency": "USD"})
        assert result["payment_id"] == "pay_98765"
        assert result["status"] == "pending"

def test_client_authentication_error() -> None:
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=401,
            json={
                "meta": {"request_id": "req_auth_fail"},
                "error": {"code": "UNAUTHORIZED", "message": "Invalid API key"}
            }
        )

    transport = httpx.MockTransport(mock_handler)
    with CryptoixClient(api_key="invalid_key", transport=transport) as client:
        with pytest.raises(CryptoixAPIError) as exc_info:
            client.list_transactions()
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.request_id == "req_auth_fail"
```

---

## Code Quality & Type Checking

To maintain production-grade reliability across the SDK, contributors must adhere to strict type annotation practices and security standards.

### Type Annotations
All public functions, client methods, and data structures must include explicit type hints. The codebase makes extensive use of `typing` constructs such as `TypedDict`, `Optional`, and type variables where appropriate.

Verify static types locally using `mypy`:

```bash
mypy src/cryptoix
```

### Security Best Practices

1. **API Key Isolation**:
   - Never hardcode API keys or test credentials into source files or commit them to source control.
   - Use environment variables (such as `CRYPTOIX_API_KEY`) as demonstrated in `examples/create_payment.py` and `examples/list_transactions.py`:
     ```python
     import os
     from cryptoix import CryptoixClient

     api_key = os.environ.get("CRYPTOIX_API_KEY", "your_api_key_here")
     client = CryptoixClient(api_key=api_key)
     ```

2. **Constant-Time Webhook Signature Verification**:
   - When verifying incoming webhooks in `src/cryptoix/webhooks.py`, always use `hmac.compare_digest` instead of standard equality operators (`==`). This protects webhook endpoints against timing side-channel attacks:
     ```python
     import hmac

     def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
         expected_signature = compute_webhook_signature(payload, secret)
         return hmac.compare_digest(expected_signature, signature)
     ```
