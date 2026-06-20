from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import write_audit_log
from app.auth.security import generate_api_key, get_key_prefix, hash_api_key
from app.billing.plans import max_keys_for_plan
from app.db.database import get_tenant_db
from app.db.redis import get_redis
from app.models import ApiKey

router = APIRouter()


class CreateApiKeyRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)


@router.get("")
async def list_api_keys(request: Request, db: AsyncSession = Depends(get_tenant_db)):
    tenant = request.state.tenant
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.tenant_id == tenant.id, ApiKey.is_active.is_(True))
        .order_by(ApiKey.created_at.desc())
    )
    return [
        {
            "id": str(key.id),
            "name": key.name,
            "prefix": key.prefix,
            "last_used": key.last_used_at.isoformat() if key.last_used_at else None,
            "created_at": key.created_at.isoformat() if key.created_at else None,
        }
        for key in result.scalars().all()
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    req: CreateApiKeyRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
):
    tenant = request.state.tenant
    count_result = await db.execute(
        select(func.count(ApiKey.id)).where(
            ApiKey.tenant_id == tenant.id,
            ApiKey.is_active.is_(True),
        )
    )
    active_count = int(count_result.scalar() or 0)
    key_limit = max_keys_for_plan(tenant.plan)
    if active_count >= key_limit:
        raise HTTPException(
            status_code=403,
            detail=f"{tenant.plan} plan allows at most {key_limit} active API keys.",
        )

    raw_key = generate_api_key()
    api_key = ApiKey(
        tenant_id=tenant.id,
        name=req.name,
        prefix=get_key_prefix(raw_key),
        key_hash=hash_api_key(raw_key),
    )
    db.add(api_key)

    await write_audit_log(
    db,
    tenant.id,
    "API_KEY_CREATED",
    req.name,
)

    await db.commit()
    await db.refresh(api_key)
    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "prefix": api_key.prefix,
        "key": raw_key,
        "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
    }


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
):
    tenant = request.state.tenant
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.tenant_id == tenant.id,
            ApiKey.is_active.is_(True),
        )
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=404, detail="API key not found.")
    api_key.is_active = False

    await write_audit_log(
    db,
    tenant.id,
    "API_KEY_REVOKED",
    api_key.name,
)

    await db.commit()
    try:
        await get_redis().delete(f"auth:{api_key.key_hash}")
    except Exception:
        pass
    return None
