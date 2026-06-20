from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.api import keys, tenants, your_api
from app.auth.middleware import AuthMiddleware
from app.billing import routes as billing_routes
from app.config import get_settings
from app.db.database import async_session_maker
from app.db.redis import close_redis
from app.models import Tenant
from app.monitoring.metrics import ACTIVE_TENANTS, UsageMetricsMiddleware, metrics_response
from app.ratelimit.limiter import RateLimitMiddleware
from app.usage.routes import router as usage_router
from app.usage.service import UsageLoggingMiddleware

settings = get_settings()

app = FastAPI(title="SaaS API Platform", version="1.0.0")

# Added in reverse execution order: CORS -> Auth -> RateLimit -> Usage logging -> metrics -> route.
app.add_middleware(UsageMetricsMiddleware)
app.add_middleware(UsageLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def update_active_tenant_metric() -> None:
    try:
        async with async_session_maker() as db:
            result = await db.execute(select(func.count(Tenant.id)))
            ACTIVE_TENANTS.set(int(result.scalar() or 0))
    except Exception:
        ACTIVE_TENANTS.set(0)


@app.on_event("shutdown")
async def shutdown() -> None:
    await close_redis()


@app.get("/")
async def root():
    return {"service": "SaaS API Platform", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    return metrics_response()


app.include_router(tenants.router, prefix="/api/tenants", tags=["tenants"])
app.include_router(keys.router, prefix="/api/keys", tags=["api keys"])
app.include_router(usage_router, prefix="/api/usage", tags=["usage"])
app.include_router(billing_routes.router, prefix="/api/billing", tags=["billing"])
app.include_router(your_api.router, prefix="/api/v1", tags=["product api"])
