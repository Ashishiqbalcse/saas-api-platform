from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.billing.plans import daily_limit_for_plan
from app.config import get_settings
from app.db.redis import get_redis
from app.monitoring.metrics import RATE_LIMIT_HITS, record_request
from app.usage.service import schedule_usage_event

ATOMIC_DAILY_COUNTER_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return { current, ttl }
"""


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int | None
    remaining: int | None
    reset_seconds: int
    used: int


def seconds_until_next_utc_midnight(now: datetime | None = None) -> int:
    current = now or datetime.now(UTC)
    next_midnight = (current + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(1, int((next_midnight - current).total_seconds()))


async def check_daily_limit(redis: Redis, tenant_id: str, plan: str) -> RateLimitDecision:
    limit = daily_limit_for_plan(plan)
    reset_seconds = seconds_until_next_utc_midnight()
    if limit is None:
        return RateLimitDecision(True, None, None, reset_seconds, 0)

    day = datetime.now(UTC).strftime("%Y%m%d")
    key = f"rate:{tenant_id}:{day}"
    used, ttl = await redis.eval(ATOMIC_DAILY_COUNTER_SCRIPT, 1, key, reset_seconds + 60)
    used = int(used)
    ttl = int(ttl if ttl and int(ttl) > 0 else reset_seconds)
    remaining = max(0, limit - used)
    return RateLimitDecision(
        allowed=used <= limit,
        limit=limit,
        remaining=remaining,
        reset_seconds=ttl,
        used=used,
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tenant = getattr(request.state, "tenant", None)
        settings = get_settings()

        if tenant is None or settings.disable_rate_limit:
            return await call_next(request)

        # Fail-open strategy:
        # If Redis is unavailable, allow requests instead of
        # taking down the entire API.
        try:
            decision = await check_daily_limit(
                get_redis(),
                str(tenant.id),
                tenant.plan,
            )
        except Exception:
            return await call_next(request)

        if not decision.allowed:
            RATE_LIMIT_HITS.labels(plan=tenant.plan).inc()

            record_request(
                request,
                status_code=429,
                plan=tenant.plan,
            )

            schedule_usage_event(
                tenant.id,
                tenant.api_key_id,
                request.url.path,
                request.method,
                0,
                429,
                0,
            )

            headers = {
                "Retry-After": str(decision.reset_seconds),
                "X-RateLimit-Limit": str(decision.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(decision.reset_seconds),
            }

            return JSONResponse(
                {
                    "detail": "Rate limit exceeded.",
                    "plan": tenant.plan,
                    "limit": decision.limit,
                    "retry_after": decision.reset_seconds,
                },
                status_code=429,
                headers=headers,
            )

        response = await call_next(request)

        if decision.limit is not None:
            response.headers["X-RateLimit-Limit"] = str(decision.limit)
            response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
            response.headers["X-RateLimit-Reset"] = str(decision.reset_seconds)

        return response
