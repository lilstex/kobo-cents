import json
from dataclasses import asdict
from datetime import datetime

from app.core.redis import redis_client
from app.integrations.market_data.base import FetchedFinancials

_TTL_SECONDS = 60 * 60 * 6  # comfortably longer than one refresh cycle takes

# Per docs/backend-architecture/02.md: avoids a redundant provider or
# research-agent call if the refresh job retries after a partial
# failure, invisible to actual user traffic, gone within a few hours
# either way.


def _key(market: str, ticker: str, cycle_id: str) -> str:
    return f"provider:{market}:{ticker}:{cycle_id}"


async def get_cached_fetch(market: str, ticker: str, cycle_id: str) -> FetchedFinancials | None:
    raw = await redis_client.get(_key(market, ticker, cycle_id))
    if raw is None:
        return None
    data = json.loads(raw)
    data["statement_date"] = datetime.fromisoformat(data["statement_date"])
    return FetchedFinancials(**data)


async def cache_fetch(market: str, ticker: str, cycle_id: str, result: FetchedFinancials) -> None:
    payload = asdict(result)
    payload["statement_date"] = result.statement_date.isoformat()
    await redis_client.set(_key(market, ticker, cycle_id), json.dumps(payload), ex=_TTL_SECONDS)
