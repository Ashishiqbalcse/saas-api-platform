from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from app.db.database import async_session_maker, set_tenant_context
from app.jobs.celery_app import celery_app
from app.models import UsageEvent


@celery_app.task(name="usage.log_event")
def log_usage_event_task(
    tenant_id: str,
    api_key_id: str | None,
    endpoint: str,
    method: str,
    latency_ms: float,
    status_code: int,
    tokens_used: int = 0,
) -> None:
    asyncio.run(
        _log_usage_event(
            tenant_id,
            api_key_id,
            endpoint,
            method,
            latency_ms,
            status_code,
            tokens_used,
        )
    )


async def _log_usage_event(
    tenant_id: str,
    api_key_id: str | None,
    endpoint: str,
    method: str,
    latency_ms: float,
    status_code: int,
    tokens_used: int = 0,
) -> None:
    async with async_session_maker() as session:
        await set_tenant_context(session, tenant_id)

        session.add(
            UsageEvent(
                tenant_id=UUID(tenant_id),
                api_key_id=UUID(api_key_id) if api_key_id else None,
                endpoint=endpoint,
                method=method,
                latency_ms=latency_ms,
                status_code=status_code,
                tokens_used=tokens_used,
                created_at=datetime.now(UTC),
            )
        )

        await session.commit()


@celery_app.task(name="usage.rollup_daily")
def rollup_daily_usage() -> dict[str, str]:
    return {"status": "ok"}