import os
from cryptoix import CryptoixClient

client = CryptoixClient(api_key=os.environ.get("CRYPTOIX_API_KEY", "ak_live_xxxxxxxxxxxx"))

payment = client.create_payment({
    "amount": 49.99,
    "order_id": "ORDER-1001",
    "callback_url": "https://example.com/webhooks/cryptoix",
})
print(payment)
