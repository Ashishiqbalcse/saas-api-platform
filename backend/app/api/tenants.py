from __future__ import annotations
from app.db.database import allow_api_key_lookup

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import write_audit_log
from app.auth.security import generate_api_key, get_key_prefix, hash_api_key
from app.db.database import get_db
from app.models import ApiKey, Tenant

router = APIRouter()


class TenantRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr


class TenantRegisterResponse(BaseModel):
    tenant_id: str
    plan: str
    api_key: str


@router.post(
    "/register",
    response_model=TenantRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_tenant(req: TenantRegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Tenant).where(Tenant.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A tenant with this email already exists.")

    raw_key = generate_api_key()
    tenant = Tenant(name=req.name, email=str(req.email), plan="free", payment_status="active")
    db.add(tenant)
    await db.flush()

    await allow_api_key_lookup(db)
    
    db.add(
        ApiKey(
            tenant_id=tenant.id,
            name="Default key",
            prefix=get_key_prefix(raw_key),
            key_hash=hash_api_key(raw_key),
        )
    )

    await write_audit_log(
        db,
        tenant.id,
        "TENANT_REGISTERED",
        f"Tenant {tenant.email} registered",
    )

    await db.commit()

    return TenantRegisterResponse(
        tenant_id=str(tenant.id),
        plan=tenant.plan,
        api_key=raw_key,
    )
