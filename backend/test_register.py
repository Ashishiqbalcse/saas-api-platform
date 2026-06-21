import asyncio

from app.models import Tenant, ApiKey
from app.auth.security import generate_api_key, get_key_prefix, hash_api_key
from app.db.database import async_session_maker

async def main():
    async with async_session_maker() as db:
        raw_key = generate_api_key()

        tenant = Tenant(
            name="Test User",
            email="test123@example.com",
            plan="free",
            payment_status="active"
        )

        db.add(tenant)
        await db.flush()

        db.add(
            ApiKey(
                tenant_id=tenant.id,
                name="Default key",
                prefix=get_key_prefix(raw_key),
                key_hash=hash_api_key(raw_key),
            )
        )

        await db.commit()

        print("SUCCESS")
        print("API KEY:", raw_key)

asyncio.run(main())