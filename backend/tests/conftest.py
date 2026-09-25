import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine


@pytest_asyncio.fixture
async def db_session():
    """Each test runs inside its own connection-bound transaction,
    the session joins it as a SAVEPOINT, and the outer transaction is
    rolled back once the test finishes. Nothing a test writes survives
    past that test, no TRUNCATE step needed, and no assumption about
    which tables exist. Verified against a real Postgres instance in
    tests/test_db_isolation.py before anything gets built on top of
    it, a broken version of exactly this kind of fixture bit the
    previous version of this project."""
    async with engine.connect() as connection:
        await connection.begin()
        session = AsyncSession(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            await session.close()
            await connection.rollback()
