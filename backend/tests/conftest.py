import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.db.session import engine, get_db
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def _clean_redis():
    """Redis isn't part of the Postgres SAVEPOINT rollback below, it
    needs its own isolation. Without this, a key one test writes (a
    staged provider fetch, a data_version counter, a rate-limit
    counter) is still sitting there for the next test, real leftover
    state caught by running the full suite together rather than one
    file at a time, exactly the kind of thing per-file test runs
    don't surface. flushdb is safe here specifically because this
    Redis instance (docker-compose's `redis` service) exists only for
    this project's local dev and test use, not shared with anything
    that would mind being flushed between tests."""
    await redis_client.flushdb()
    yield


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


@pytest_asyncio.fixture
async def client(db_session):
    """An async client wired to the same rolled-back session as
    db_session, per FastAPI's own dependency-override pattern.
    Without this, an API-level test would hit app.db.session.get_db's
    real, independent engine and genuinely commit to the dev database,
    the whole point of the isolation fixture above would be bypassed
    the moment a test goes through the actual HTTP layer instead of
    calling a function directly.

    httpx.AsyncClient with ASGITransport, not starlette's TestClient,
    deliberately: TestClient runs the app in a background thread with
    its own event loop, and an asyncpg connection is bound to the loop
    it was created on, handing that connection across the thread/loop
    boundary breaks with a "Future attached to a different loop" error.
    Staying fully async end to end avoids the boundary entirely.

    Rate limiting is covered by the _clean_redis fixture above too:
    SlowAPI's storage is the same Redis, flushed clean before every
    test, so the signup rate limit never trips against the test suite
    itself, only real abuse."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
    finally:
        app.dependency_overrides.pop(get_db, None)
