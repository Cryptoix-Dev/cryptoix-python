---
title: USAGE
slug: usage
lang: en
project: Cryptoix-python
domain: https://github.com/Cryptoix-Dev/cryptoix-python
generated_by: agenter
---
# Developer Documentation & Usage Guide

Welcome to the technical documentation for `cryptoix-python`, the official Python SDK for interacting with the Cryptoix Merchant and Payment APIs. This guide covers installation, client lifecycle management, core merchant workflows, pagination, and security best practices.

---

## Installation & Setup

`cryptoix-python` uses modern Python packaging standards governed by PEP 517/621 with Hatchling as the backend build system. 

Install the package directly from your project environment using pip:

```bash
pip install cryptoix-python
```

### Security Best Practices: API Keys

Never hardcode your API keys directly into source control. Always load your credentials securely from environment variables or a secure vault. The SDK automatically detects the `CRYPTOIX_API_KEY` environment variable if explicit parameters are omitted during initialization:

```bash
export CRYPTOIX_API_KEY="cix_live_abc123xyz789"
```

---

## Client Initialization & Lifecycle

The SDK provides the `CryptoixClient` class (`src/cryptoix/client.py`) to manage API communication, header injection, automatic retry behavior for rate limits (`429`), and response envelope unwrapping.

### The Context Manager Pattern

Always use the context manager pattern (`with CryptoixClient(...) as client:`) for automated HTTP session management and cleanup.

```python
import os
from cryptoix import CryptoixClient, CryptoixAPIError

# API key is automatically read from the CRYPTOIX_API_KEY environment variable,
# or you can supply it explicitly: api_key=os.getenv("CRYPTOIX_API_KEY")
with CryptoixClient() as client:
    try:
        # Perform API operations here
        pass
    except CryptoixAPIError as e:
        print(f"API Error [{e.status_code}] {e.code}: {e.details} (Request ID: {e.request_id})")
```

---

## Creating & Fetching Payments

Use `CryptoixClient.create_payment()` to initiate payment orders for your merchant workflow.

```python
from cryptoix import CryptoixClient

with CryptoixClient() as client:
    payment = client.create_payment(
        amount=150.00,
        currency="USD",
        merchant_reference="INV-2023-001",
        description="Enterprise Subscription Tier"
    )
    
    print(f"Payment Created Successfully!")
    print(f"Payment ID: {payment.get('id')}")
    print(f"Checkout URL: {payment.get('checkout_url')}")
```

---

## Listing Transactions & Pagination

When querying transaction histories, the SDK uses the frozen `Pagination` dataclass (`src/cryptoix/pagination.py`) to manage paging parameters (`page` defaults to `1`, and `per_page` controls items per page).

```python
from cryptoix import CryptoixClient
from cryptoix.pagination import Pagination

with CryptoixClient() as client:
    # Configure pagination parameters (page 1, 20 items per page)
    pagination = Pagination(page=1, per_page=20)
    
    response = client.list_transactions(pagination=pagination)
    
    print(f"Fetched {len(response.get('items', []))} transactions.")
```

---

## Payouts & Customer Refunds

Manage merchant disbursements and issue customer refunds using dedicated client operations.

```python
from cryptoix import CryptoixClient
from cryptoix import CryptoixValidationError

with CryptoixClient() as client:
    try:
        # Issue a customer refund
        refund = client.create_refund(
            payment_id="pay_987654321",
            amount=50.00,
            reason="Customer requested cancellation"
        )
        print(f"Refund processed: {refund.get('refund_id')}")

        # Execute a merchant payout
        payout = client.create_payout(
            destination_address="0x1234...abcd",
            amount=500.00,
            currency="USDT"
        )
        print(f"Payout initiated: {payout.get('payout_id')}")

    except CryptoixValidationError as e:
        print(f"Validation failed: {e.details}")
```

---

## Escrow & Invoice Management

Handle complex escrow arrangements and automated invoice lifecycles through the client interface.

```python
from cryptoix import CryptoixClient

with CryptoixClient() as client:
    # Create an escrow contract
    escrow = client.create_escrow(
        buyer_id="usr_buyer_123",
        seller_id="usr_seller_456",
        amount=1200.00,
        currency="USD"
    )
    print(f"Escrow established: {escrow.get('escrow_id')}")

    # Generate an invoice
    invoice = client.create_invoice(
        customer_email="client@example.com",
        items=[{"name": "Consulting Services", "price": 300.00, "quantity": 2}],
        due_date="2023-12-31"
    )
    print(f"Invoice generated: {invoice.get('invoice_url')}")
```

---

## Generating Payment QR Codes

Generate dynamic QR codes for point-of-sale or crypto address payments utilizing the QR service endpoint (`DEFAULT_QR_URL`).

```python
from cryptoix import CryptoixClient

with CryptoixClient() as client:
    qr_data = client.generate_payment_qr(
        payment_id="pay_123456789",
        size=300
    )
    
    print(f"QR Code Image URL: {qr_data.get('qr_image_url')}")
```

---

## Webhook Verification & Security

Incoming webhook payloads from Cryptoix must be validated to ensure authenticity and protect against forgery. 

### Constant-Time Signature Verification

The `webhooks` module (`src/cryptoix/webhooks.py`) exposes `verify_webhook_signature()`, which internally uses `hmac.compare_digest` to execute constant-time comparisons. This prevents timing side-channel attacks.

```python
from cryptoix import verify_webhook_signature

# Example HTTP webhook handler context (e.g., Flask, FastAPI, or Django)
def handle_webhook(request_body: bytes, signature_header: str) -> bool:
    webhook_secret = "whsec_your_secret_key_here"
    
    # Verifies the HMAC-SHA256 signature securely
    is_valid = verify_webhook_signature(
        payload=request_body,
        signature=signature_header,
        secret=webhook_secret
    )
    
    if not is_valid:
        return False
        
    # Process verified event payload...
    return True
```

---

## Exception Handling Reference

The SDK maps HTTP and validation issues to a clear exception hierarchy (`src/cryptoix/errors.py`), allowing you to catch specific failure modes cleanly:

* `CryptoixAPIError`: Base exception storing `status_code`, error `code`, `details`, and `request_id`.
* `CryptoixAuthenticationError`: Triggered on HTTP `401` or `403` authorization failures.
* `CryptoixValidationError`: Triggered on invalid input payloads or HTTP `422`.
* `CryptoixRateLimitError`: Captures rate limiting (`429`) and exposes `retry_after` values.

```python
from cryptoix import CryptoixClient, CryptoixAuthenticationError, CryptoixRateLimitError, CryptoixAPIError

with CryptoixClient() as client:
    try:
        client.list_transactions()
    except CryptoixAuthenticationError as e:
        print(f"Authentication failed: {e.details} (Status: {e.status_code})")
    except CryptoixRateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after} seconds.")
    except CryptoixAPIError as e:
        print(f"General API error [{e.code}]: {e.details}")
```
