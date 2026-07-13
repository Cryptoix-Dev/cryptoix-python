import os
from cryptoix import CryptoixClient

client = CryptoixClient(api_key=os.environ.get("CRYPTOIX_API_KEY", "ak_live_xxxxxxxxxxxx"))
transactions = client.list_transactions(page=1, per_page=25)
print(transactions)
