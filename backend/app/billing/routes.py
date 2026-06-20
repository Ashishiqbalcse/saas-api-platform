from __future__ import annotations

from uuid import UUID

import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from app.audit import write_audit_log
from app.billing.plans import PLANS
from app.billing.webhooks import construct_stripe_event
from app.config import get_settings
from app.db.database import async_session_maker
from app.models import (
    ProcessedWebhook,
    SubscriptionHistory,
    Tenant,
)

router = APIRouter()


class CheckoutRequest(BaseModel):
    plan: str


def price_id_for_plan(plan: str) -> str | None:
    settings = get_settings()
    return {
        "pro": settings.stripe_price_pro,
        "enterprise": settings.stripe_price_enterprise,
    }.get(plan)


@router.post("/checkout")
async def create_checkout_session(
    req: CheckoutRequest,
    request: Request,
):
    if req.plan not in {"pro", "enterprise"}:
        raise HTTPException(status_code=400, detail="Checkout is only available for paid plans.")

    tenant = request.state.tenant
    price_id = price_id_for_plan(req.plan)
    settings = get_settings()
    if settings.stripe_test_mode or not settings.stripe_secret_key or not price_id:
        return {
            "checkout_url": f"{settings.app_url}/billing?success=1&plan={req.plan}",
            "test_mode": True,
        }

    stripe.api_key = settings.stripe_secret_key
    checkout_args = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": f"{settings.app_url}/billing?success=1&session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{settings.app_url}/billing?cancelled=1",
        "metadata": {"tenant_id": str(tenant.id), "plan": req.plan},
        "subscription_data": {"metadata": {"tenant_id": str(tenant.id), "plan": req.plan}},
    }
    if tenant.stripe_customer_id:
        checkout_args["customer"] = tenant.stripe_customer_id
    else:
        checkout_args["customer_email"] = tenant.email

    session = stripe.checkout.Session.create(**checkout_args)
    return {"checkout_url": session.url}


@router.post("/portal")
async def create_billing_portal(request: Request):
    tenant = request.state.tenant
    settings = get_settings()
    if settings.stripe_test_mode or not tenant.stripe_customer_id:
        return {"portal_url": f"{settings.app_url}/billing", "test_mode": True}

    stripe.api_key = settings.stripe_secret_key
    portal_session = stripe.billing_portal.Session.create(
        customer=tenant.stripe_customer_id,
        return_url=f"{settings.app_url}/billing",
    )
    return {"portal_url": portal_session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    settings = get_settings()
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    try:
        event = construct_stripe_event(payload, signature, settings.stripe_webhook_secret)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid Stripe webhook: {exc}") from exc

    await apply_stripe_event(event)
    return {"received": True}


async def apply_stripe_event(event) -> None:
    event_id = event.get("id")

    if not event_id:
        return

    async with async_session_maker() as db:
        existing = await db.execute(
            select(ProcessedWebhook).where(
            ProcessedWebhook.event_id == event_id
        )
    )

    if existing.scalar_one_or_none():
        return

    db.add(
        ProcessedWebhook(
            event_id=event_id
        )
    )

    await db.commit()
    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        metadata = obj.get("metadata") or {}
        tenant_id = metadata.get("tenant_id")
        plan = metadata.get("plan")
        if tenant_id and plan in PLANS:
            async with async_session_maker() as db:
                tenant = await db.get(Tenant, UUID(tenant_id))
                if tenant:
                    previous_plan = tenant.plan

                tenant.plan = plan

                db.add(
        SubscriptionHistory(
            tenant_id=tenant.id,
            previous_plan=previous_plan,
            new_plan=plan,
        )
    )

    tenant.payment_status = "active"
    tenant.stripe_customer_id = (
        obj.get("customer")
        or tenant.stripe_customer_id
    )
    tenant.stripe_subscription_id = (
        obj.get("subscription")
        or tenant.stripe_subscription_id
    )

    await db.commit()

    if event_type == "customer.subscription.updated":
        metadata = obj.get("metadata") or {}
        plan = metadata.get("plan")
        tenant_id = metadata.get("tenant_id")
        async with async_session_maker() as db:
            tenant = None
            if tenant_id:
                tenant = await db.get(Tenant, UUID(tenant_id))
            if tenant is None and obj.get("customer"):
                result = await db.execute(
                    select(Tenant).where(Tenant.stripe_customer_id == obj.get("customer"))
                )
                tenant = result.scalar_one_or_none()
            if tenant and plan in PLANS:
                previous_plan = tenant.plan

                tenant.plan = plan

                db.add(
        SubscriptionHistory(
            tenant_id=tenant.id,
            previous_plan=previous_plan,
            new_plan=plan,
        )
    )

    tenant.payment_status = (
        "active"
        if obj.get("status") == "active"
        else "past_due"
    )

    tenant.stripe_subscription_id = (
        obj.get("id")
        or tenant.stripe_subscription_id
    )

    await db.commit()

    if event_type in {"customer.subscription.deleted", "invoice.payment_failed"}:
        customer_id = obj.get("customer")

        async with async_session_maker() as db:
            result = await db.execute(
                select(Tenant).where(
                    Tenant.stripe_customer_id == customer_id
                )
            )

            tenant = result.scalar_one_or_none()

            if tenant:

                tenant.payment_status = (
        "past_due"
        if event_type == "invoice.payment_failed"
        else "canceled"
    )

    if event_type == "invoice.payment_failed":
        await write_audit_log(
            db,
            tenant.id,
            "PAYMENT_FAILED",
            customer_id,
        )

    if event_type == "customer.subscription.deleted":

        db.add(
            SubscriptionHistory(
                tenant_id=tenant.id,
                previous_plan=tenant.plan,
                new_plan="free",
            )
        )

        tenant.plan = "free"
        tenant.stripe_subscription_id = None

        await write_audit_log(
            db,
            tenant.id,
            "SUBSCRIPTION_CANCELED",
            customer_id,
        )

    await db.commit()
