from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.plans import daily_limit_for_plan
from app.db.database import get_tenant_db
from app.models import UsageEvent
from app.ratelimit.limiter import seconds_until_next_utc_midnight

router = APIRouter()


@router.get("/summary")
async def usage_summary(request: Request, db: AsyncSession = Depends(get_tenant_db)):
    tenant = request.state.tenant
    now = datetime.now(UTC)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    limit = daily_limit_for_plan(tenant.plan)
    result = await db.execute(
        select(func.count(UsageEvent.id)).where(
            UsageEvent.tenant_id == tenant.id,
            UsageEvent.created_at >= start,
        )
    )
    today_requests = int(result.scalar() or 0)
    remaining = None if limit is None else max(0, limit - today_requests)
    return {
        "tenant_id": str(tenant.id),
        "tenant_name": tenant.name,
        "plan": tenant.plan,
        "payment_status": tenant.payment_status,
        "today_requests": today_requests,
        "daily_limit": limit,
        "remaining_today": remaining,
        "resets_in": seconds_until_next_utc_midnight(now),
    }


@router.get("/daily")
async def daily_usage(request: Request, db: AsyncSession = Depends(get_tenant_db)):
    tenant = request.state.tenant
    start = datetime.now(UTC) - timedelta(days=30)
    result = await db.execute(
        select(
            func.date_trunc("day", UsageEvent.created_at).label("day"),
            func.count(UsageEvent.id).label("requests"),
            func.sum(UsageEvent.tokens_used).label("tokens"),
            func.avg(UsageEvent.latency_ms).label("avg_latency_ms"),
        )
        .where(UsageEvent.tenant_id == tenant.id, UsageEvent.created_at >= start)
        .group_by("day")
        .order_by("day")
    )
    return [
        {
            "date": row.day.date().isoformat(),
            "requests": int(row.requests or 0),
            "tokens": int(row.tokens or 0),
            "avg_latency_ms": round(float(row.avg_latency_ms or 0), 2),
        }
        for row in result.all()
    ]


@router.get("/endpoints")
async def endpoint_usage(request: Request, db: AsyncSession = Depends(get_tenant_db)):
    tenant = request.state.tenant
    start = datetime.now(UTC) - timedelta(days=7)
    result = await db.execute(
        select(
            UsageEvent.endpoint,
            func.count(UsageEvent.id).label("requests"),
            func.avg(UsageEvent.latency_ms).label("avg_latency_ms"),
            func.sum(case((UsageEvent.status_code >= 500, 1), else_=0)).label("errors"),
        )
        .where(UsageEvent.tenant_id == tenant.id, UsageEvent.created_at >= start)
        .group_by(UsageEvent.endpoint)
        .order_by(desc("requests"))
        .limit(10)
    )
    return [
        {
            "endpoint": row.endpoint,
            "requests": int(row.requests or 0),
            "avg_latency_ms": round(float(row.avg_latency_ms or 0), 2),
            "errors": int(row.errors or 0),
        }
        for row in result.all()
    ]
