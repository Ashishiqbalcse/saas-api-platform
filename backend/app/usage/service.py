from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import get_settings
from app.db.database import async_session_maker, set_tenant_context
from app.jobs.tasks import log_usage_event_task
from app.models import UsageEvent
from app.monitoring.metrics import route_template


async def log_usage_event(
    tenant_id: UUID,
    api_key_id: UUID | None,
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
                tenant_id=tenant_id,
                api_key_id=api_key_id,
                endpoint=endpoint,
                method=method,
                latency_ms=latency_ms,
                status_code=status_code,
                tokens_used=tokens_used,
                created_at=datetime.now(UTC),
            )
        )
        await session.commit()


async def safe_log_usage_event(*args, **kwargs) -> None:
    try:
        await log_usage_event(*args, **kwargs)
    except Exception:
        pass


def schedule_usage_event(
    tenant_id,
    api_key_id,
    endpoint,
    method,
    latency_ms,
    status_code,
    tokens_used=0,
) -> None:
    try:
        log_usage_event_task.delay(
            str(tenant_id),
            str(api_key_id) if api_key_id else None,
            endpoint,
            method,
            latency_ms,
            status_code,
            tokens_used,
        )
    except Exception:
        pass


class UsageLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = datetime.now(UTC)
        try:
            response = await call_next(request)
        except Exception:
            tenant = getattr(request.state, "tenant", None)
            if tenant is not None:
                latency_ms = (datetime.now(UTC) - start).total_seconds() * 1000
                schedule_usage_event(
                    tenant.id,
                    tenant.api_key_id,
                    route_template(request),
                    request.method,
                    latency_ms,
                    500,
                    getattr(request.state, "tokens_used", 0),
                )
            raise

        tenant = getattr(request.state, "tenant", None)
        if tenant is not None:
            latency_ms = (datetime.now(UTC) - start).total_seconds() * 1000
            if get_settings().usage_log_inline:
                await log_usage_event(
                    tenant.id,
                    tenant.api_key_id,
                    route_template(request),
                    request.method,
                    latency_ms,
                    response.status_code,
                    getattr(request.state, "tokens_used", 0),
                )
            else:
                schedule_usage_event(
                    tenant.id,
                    tenant.api_key_id,
                    route_template(request),
                    request.method,
                    latency_ms,
                    response.status_code,
                    getattr(request.state, "tokens_used", 0),
                )
        return response
