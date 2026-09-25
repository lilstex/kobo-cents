from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Connection pooling per docs/backend-architecture/00.md's latency
# section: the pool is reused across requests instead of opening a
# fresh connection per request.
engine = create_async_engine(
    settings.database_url, pool_pre_ping=True, pool_size=10, max_overflow=10
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
