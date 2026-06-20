from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth.security import get_key_prefix, hash_api_key, verify_api_key
from app.auth.types import AuthenticatedTenant
from app.config import get_settings
from app.db.database import allow_api_key_lookup, async_session_maker
from app.db.redis import get_redis
from app.models import ApiKey, Tenant
from app.monitoring.metrics import record_request


def is_public_path(path: str) -> bool:
    settings = get_settings()
    return any(path == public or path.startswith(f"{public}/") for public in settings.public_paths)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or is_public_path(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            record_request(request, status_code=401, plan="anonymous")
            return JSONResponse({"detail": "Missing Bearer API key."}, status_code=401)

        raw_key = auth_header.split(" ", 1)[1].strip()
        tenant = await self._authenticate(raw_key)
        if tenant is None:
            record_request(request, status_code=401, plan="anonymous")
            return JSONResponse({"detail": "Invalid or revoked API key."}, status_code=401)

        request.state.tenant = tenant
        return await call_next(request)

    async def _authenticate(self, raw_key: str) -> AuthenticatedTenant | None:
        key_hash = hash_api_key(raw_key)
        cache_key = f"auth:{key_hash}"
        settings = get_settings()

        try:
            cached = await get_redis().get(cache_key)
            if cached:
                data = json.loads(cached)
                data["id"] = UUID(data["id"])
                data["api_key_id"] = UUID(data["api_key_id"])
                return AuthenticatedTenant(**data)
        except Exception:
            cached = None

        prefix = get_key_prefix(raw_key)
        async with async_session_maker() as session:
            await allow_api_key_lookup(session)
            rows = await session.execute(
                select(ApiKey, Tenant)
                .join(Tenant, ApiKey.tenant_id == Tenant.id)
                .where(ApiKey.prefix == prefix, ApiKey.is_active.is_(True))
            )
            for api_key, tenant in rows.all():
                if verify_api_key(raw_key, api_key.key_hash):
                    api_key.last_used_at = datetime.now(UTC)
                    await session.commit()
                    auth_tenant = AuthenticatedTenant(
                        id=tenant.id,
                        name=tenant.name,
                        email=tenant.email,
                        plan=tenant.plan,
                        payment_status=tenant.payment_status,
                        api_key_id=api_key.id,
                        api_key_hash=api_key.key_hash,
                        stripe_customer_id=tenant.stripe_customer_id,
                    )
                    try:
                        await get_redis().setex(
                            cache_key,
                            settings.auth_cache_ttl_seconds,
                            json.dumps(
                                {
                                    "id": str(auth_tenant.id),
                                    "name": auth_tenant.name,
                                    "email": auth_tenant.email,
                                    "plan": auth_tenant.plan,
                                    "payment_status": auth_tenant.payment_status,
                                    "api_key_id": str(auth_tenant.api_key_id),
                                    "api_key_hash": auth_tenant.api_key_hash,
                                    "stripe_customer_id": auth_tenant.stripe_customer_id,
                                }
                            ),
                        )
                    except Exception:
                        pass
                    return auth_tenant

        return None
