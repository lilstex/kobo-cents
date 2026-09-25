import json

from app.core.redis import redis_client

# The read-path cache's safety-net TTL, per 02.md: not the real
# invalidation mechanism (the version bump above is), just a backstop
# so a bug that fails to bump the version doesn't leave stale data
# sitting there indefinitely. Comfortably longer than the gap between
# refresh cycles (two to three times a day).
_READ_CACHE_TTL_SECONDS = 60 * 60 * 12

# The read-path cache versioning scheme from docs/backend-architecture/
# 02.md: every cache key for the market overview and stock detail
# pages includes this version. Bumping it after a refresh commits
# makes every future request for that market ask for a key name that
# doesn't exist yet, an immediate, guaranteed cache miss that rebuilds
# from current data, rather than a blind TTL guessing how long "fresh
# enough" should be.


def _version_key(market: str) -> str:
    return f"data_version:{market}"


async def get_data_version(market: str) -> int:
    value = await redis_client.get(_version_key(market))
    return int(value) if value is not None else 0


async def bump_data_version(market: str) -> int:
    return await redis_client.incr(_version_key(market))


async def get_cached_json(key: str) -> dict | None:
    raw = await redis_client.get(key)
    return json.loads(raw) if raw is not None else None


async def set_cached_json(key: str, value: dict) -> None:
    await redis_client.set(key, json.dumps(value), ex=_READ_CACHE_TTL_SECONDS)
