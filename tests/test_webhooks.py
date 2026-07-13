from cryptoix.webhooks import compute_webhook_signature, verify_webhook_signature

PAYLOAD = b'{"uuid":"tx_test_123","status":"completed","amount_fiat":100,"timestamp":1780574400}'
SECRET = "whsec_test_secret_1234567890"
SIGNATURE = "9bc6d23d70a52f2960d404a6bf2fd067ee8f15e2e30c4e53cfde3559251a7e25"


def test_signature_vector():
    assert compute_webhook_signature(PAYLOAD, SECRET) == SIGNATURE
    assert verify_webhook_signature(PAYLOAD, SIGNATURE, SECRET)
    assert not verify_webhook_signature(PAYLOAD, "bad", SECRET)
