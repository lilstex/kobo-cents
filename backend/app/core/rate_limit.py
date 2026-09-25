from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Fixed-window counters backed by Redis, per docs/backend-architecture/
# 01.md: the right cost/accuracy tradeoff for signup and share-link
# abuse specifically, not a case that needs sliding-window precision.
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)
