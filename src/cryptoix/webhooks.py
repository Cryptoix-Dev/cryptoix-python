from __future__ import annotations

import hmac
import hashlib
from typing import Union

BytesLike = Union[bytes, bytearray, memoryview]


def compute_webhook_signature(payload: Union[str, BytesLike], secret: str) -> str:
    raw = payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)
    return hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()


def verify_webhook_signature(payload: Union[str, BytesLike], signature: str, secret: str) -> bool:
    expected = compute_webhook_signature(payload, secret)
    return hmac.compare_digest(expected, signature or "")
