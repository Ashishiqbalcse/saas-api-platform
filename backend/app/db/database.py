from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def set_tenant_context(session: AsyncSession, tenant_id: UUID | str) -> None:
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )


async def allow_api_key_lookup(session: AsyncSession) -> None:
    await session.execute(text("SELECT set_config('app.allow_api_key_lookup', 'on', true)"))


async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def get_tenant_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        await set_tenant_context(session, request.state.tenant.id)
        yield session
