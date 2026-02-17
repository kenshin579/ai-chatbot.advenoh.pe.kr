from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

engine = None
async_session_factory = None


async def init_db(database_url: str) -> None:
    global engine, async_session_factory
    engine = create_async_engine(database_url, pool_pre_ping=True)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


async def close_db() -> None:
    global engine
    if engine:
        await engine.dispose()
        engine = None
