## Webhook Overview

Webhooks allow the Cryptoix platform to send real-time HTTP notifications to your backend server when events occur (such as successful payments, processed payouts, or invoice status updates). 

When an event takes place, Cryptoix makes an HTTP `POST` request to your configured webhook endpoint. To ensure security, authenticity, and integrity, every outgoing webhook request includes a cryptographic signature in its headers. Your backend service must inspect this signature before processing the event payload.

The `cryptoix-python` SDK provides dedicated utilities within `src/cryptoix/webhooks.py` to handle webhook signature verification safely and reliably.

---

## HMAC-SHA256 Signature Verification

Cryptoix signs webhook payloads using an **HMAC-SHA256** hash-based message authentication code. 

1. When Cryptoix transmits a webhook, it computes an HMAC-SHA256 hash of the raw HTTP request body using your webhook secret as the private key.
2. The resulting hex digest is sent in the request headers (typically via `X-Cryptoix-Signature`).
3. Your application captures the raw, unparsed request body bytes and the signature header value, passing them alongside your webhook secret to `verify_webhook_signature`.

### Key SDK Functions

- `compute_webhook_signature(payload: bytes | str, secret: str) -> str`: Computes the expected HMAC-SHA256 hex digest for a given payload and secret.
- `verify_webhook_signature(payload: bytes | str, signature: str, secret: str) -> bool`: Validates an incoming signature against a payload and secret, returning `True` if valid and `False` otherwise.

---

## Constant-Time Verification Security

When validating cryptographic signatures in network services, standard string comparison operators (like `==`) are vulnerable to **timing attacks**. An attacker can measure the time it takes for your server to respond to different signatures, eventually deducing the correct signature byte-by-byte.

To prevent this timing side-channel vulnerability, `cryptoix-python` relies on Python's standard library `hmac.compare_digest`:

```python
import hmac

def verify_webhook_signature(payload: bytes | str, signature: str, secret: str) -> bool:
    expected = compute_webhook_signature(payload, secret)
    return hmac.compare_digest(expected, signature)
```

`hmac.compare_digest` performs a fixed-time comparison regardless of where differences occur in the strings, effectively neutralizing timing-based side-channel analysis.

> **Security Best Practice:** Never store webhook secrets or API keys directly in source control or configuration files committed to public repositories. Load these credentials securely using environment variables or dedicated secret management solutions.

---

## End-to-End Webhook Handler Example

Below is a complete, production-ready example demonstrating how to implement a secure webhook receiver endpoint using **FastAPI** and the `cryptoix-python` SDK.

This example explicitly reads raw request body bytes to ensure that payload transformations (such as JSON parsing before verification) do not alter the signature.

```python
import os
from fastapi import FastAPI, Header, HTTPException, Request, status
from cryptoix import verify_webhook_signature

app = FastAPI()

# Load the webhook secret securely from environment variables
WEBHOOK_SECRET = os.getenv("CRYPTOIX_WEBHOOK_SECRET", "whsec_your_secret_here")

@app.post("/webhook/cryptoix")
async def cryptoix_webhook_receiver(
    request: Request,
    x_cryptoix_signature: str = Header(..., description="Signature header sent by Cryptoix")
) -> dict:
    """
    Secure webhook endpoint for receiving and verifying Cryptoix events.
    """
    # 1. Retrieve the raw request body as bytes.
    # CRITICAL: Do not parse JSON before verifying the signature, 
    # as whitespace or key ordering changes will invalidate the HMAC hash.
    payload_bytes = await request.body()

    # 2. Verify the webhook signature using constant-time comparison
    is_valid = verify_webhook_signature(
        payload=payload_bytes,
        signature=x_cryptoix_signature,
        secret=WEBHOOK_SECRET
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature."
        )

    # 3. Safe to parse and process the verified payload
    event_data = await request.json()
    event_type = event_data.get("type")
    
    # Handle the event according to your application logic
    print(f"Successfully processed verified event: {event_type}")

    return {"status": "success"}
```
