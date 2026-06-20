from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AuthenticatedTenant:
    id: UUID
    name: str
    email: str
    plan: str
    payment_status: str
    api_key_id: UUID
    api_key_hash: str
    stripe_customer_id: str | None = None
