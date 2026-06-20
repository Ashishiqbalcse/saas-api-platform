from __future__ import annotations

import stripe


def construct_stripe_event(payload: bytes, signature: str | None, webhook_secret: str):
    if not signature:
        raise ValueError("Missing Stripe-Signature header.")
    return stripe.Webhook.construct_event(payload, signature, webhook_secret)
