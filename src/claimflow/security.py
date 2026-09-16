from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

PII_FIELDS = {"customer_name", "customer_email", "claimant_name", "claimant_email", "payee_name"}


def tokenization_key() -> bytes:
    return os.getenv("CLAIMFLOW_TOKENIZATION_KEY", "development-only-key").encode()


def deterministic_token(value: str, *, key: bytes | None = None) -> str:
    """Create a stable, non-reversible token suitable for joins in this demo."""
    digest = hmac.new(key or tokenization_key(), value.strip().lower().encode(), hashlib.sha256)
    return f"tok_{digest.hexdigest()[:24]}"


def protect_pii(payload: dict[str, Any]) -> dict[str, Any]:
    protected: dict[str, Any] = {}
    for field, value in payload.items():
        if field in PII_FIELDS:
            protected[f"{field}_token"] = deterministic_token(str(value))
        else:
            protected[field] = value
    return protected
