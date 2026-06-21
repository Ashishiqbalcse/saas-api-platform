from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def write_audit_log(
    db: AsyncSession,
    tenant_id,
    event_type: str,
    event_data: str | None = None,
):
    db.add(
        AuditLog(
            tenant_id=tenant_id,
            event_type=event_type,
            event_data=event_data,
        )
    )

    db.add(
    AuditLog(
        tenant_id=tenant_id,
        event_type=event_type,
        event_data=event_data,
    )
)