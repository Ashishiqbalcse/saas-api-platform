import asyncio
from sqlalchemy import text
from app.db.database import async_session_maker

async def main():
    async with async_session_maker() as db:
        result = await db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            ORDER BY table_name;
        """))

        for row in result:
            print(row[0])

asyncio.run(main())