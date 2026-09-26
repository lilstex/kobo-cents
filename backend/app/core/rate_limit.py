from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Fixed-window counters backed by Redis, per docs/backend-architecture/
# 01.md: the right cost/accuracy tradeoff for signup and share-link
# abuse specifically, not a case that needs sliding-window precision.
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)

# Named tiers, per docs/backend-architecture/03-phases.md's Sub-phase
# 10.1: general rate limiting across every authenticated endpoint, not
# just signup and share-link creation, so a compromised or scripted
# account can't hammer the backend or the underlying market-data
# providers through any other route. Three tiers, not a bespoke number
# per endpoint: cheap reads get room to actually be used, mutations
# get a real ceiling, and the small set of endpoints an attacker would
# actually want to brute-force (login, verification, password reset)
# get the tightest one, independent of and in addition to whatever
# specific limit an endpoint already had its own real reason to set
# (signup's 5/hour, share viewing's 30/hour).
READ_LIMIT = "120/minute"
WRITE_LIMIT = "30/minute"
AUTH_SENSITIVE_LIMIT = "10/hour"
