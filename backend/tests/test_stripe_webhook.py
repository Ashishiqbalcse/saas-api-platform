import hashlib
import hmac
import json
import time

import pytest
import stripe

from app.billing.webhooks import construct_stripe_event


def signed_header(payload: bytes, secret: str) -> str:
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload.decode()}".encode()
    signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def test_construct_stripe_event_accepts_valid_signature():
    secret = "whsec_test"
    payload = json.dumps({"id": "evt_test", "type": "checkout.session.completed"}).encode()
    event = construct_stripe_event(payload, signed_header(payload, secret), secret)
    assert event["id"] == "evt_test"


def test_construct_stripe_event_rejects_invalid_signature():
    payload = b'{"id":"evt_test"}'
    with pytest.raises(stripe.SignatureVerificationError):
        construct_stripe_event(payload, "t=1,v1=bad", "whsec_test")
