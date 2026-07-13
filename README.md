# Cryptoix Python SDK

Official Python SDK for the Cryptoix.io Merchant API.

## Install

```bash
pip install cryptoix
```

## Quick start

```python
from cryptoix import CryptoixClient

client = CryptoixClient(api_key="ak_live_xxxxxxxxxxxx")
payment = client.create_payment({"amount": 49.99, "order_id": "ORDER-1001"})
print(payment)
```

## Environment configuration

```python
import os
from cryptoix import CryptoixClient

client = CryptoixClient(api_key=os.environ["CRYPTOIX_API_KEY"])
```

## Webhook verification

```python
from cryptoix.webhooks import verify_webhook_signature

ok = verify_webhook_signature(raw_body, signature, webhook_secret)
```

Never send API keys in query strings. Use `Authorization: Bearer` or `X-API-Key` headers only.
