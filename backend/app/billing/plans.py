from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    key: str
    daily_request_limit: int | None
    max_api_keys: int
    monthly_price: str


PLANS: dict[str, Plan] = {
    "free": Plan("free", daily_request_limit=100, max_api_keys=2, monthly_price="0"),
    "pro": Plan("pro", daily_request_limit=10_000, max_api_keys=10, monthly_price="999"),
    "enterprise": Plan(
        "enterprise", daily_request_limit=None, max_api_keys=100, monthly_price="7999"
    ),
}


def get_plan(plan_key: str) -> Plan:
    return PLANS.get(plan_key, PLANS["free"])


def daily_limit_for_plan(plan_key: str) -> int | None:
    return get_plan(plan_key).daily_request_limit


def max_keys_for_plan(plan_key: str) -> int:
    return get_plan(plan_key).max_api_keys
