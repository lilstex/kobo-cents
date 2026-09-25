import pytest_asyncio
from sqlalchemy import text

from app.db.session import engine

# A throwaway table, created outside any per-test transaction (DDL is
# transactional in Postgres, so it can't live inside the same
# transaction the db_session fixture rolls back, or it would vanish
# before the second test ever ran). Exists only to prove the fixture
# actually isolates tests, per Sub-phase 0.2 of
# docs/backend-architecture/03-phases.md; no product code depends on
# this table.


@pytest_asyncio.fixture(scope="module", autouse=True)
async def scratch_table():
    async with engine.begin() as connection:
        await connection.execute(text("CREATE TABLE IF NOT EXISTS _isolation_check (value TEXT)"))
    yield
    async with engine.begin() as connection:
        await connection.execute(text("DROP TABLE IF EXISTS _isolation_check"))


async def test_write_a_row(db_session):
    await db_session.execute(text("INSERT INTO _isolation_check (value) VALUES ('leftover')"))
    await db_session.flush()
    result = await db_session.execute(text("SELECT value FROM _isolation_check"))
    assert result.scalars().all() == ["leftover"]


async def test_previous_test_did_not_leak(db_session):
    result = await db_session.execute(text("SELECT value FROM _isolation_check"))
    assert result.scalars().all() == []
