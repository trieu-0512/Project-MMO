import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.models import Base
from app.db.session import engine


async def init_models(db_engine: AsyncEngine | None = None) -> None:
    eng = db_engine or engine
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_models())
