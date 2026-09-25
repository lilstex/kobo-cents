import logging

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.favorites import router as favorites_router
from app.api.v1.market import router as market_router
from app.core.config import settings
from app.core.logging import configure_logging, new_request_id, request_id_var
from app.core.rate_limit import limiter

configure_logging()
logger = logging.getLogger("app")

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

app = FastAPI(title="Kobo & Cents API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(market_router, prefix="/api/v1")
app.include_router(favorites_router, prefix="/api/v1")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Every log line for this request carries the same id, whether
    it came in on the header (a request forwarded from somewhere that
    already assigned one) or gets generated fresh here, per
    docs/backend-architecture/03-phases.md's Sub-phase 0.3."""
    request_id = request.headers.get("x-request-id", new_request_id())
    token = request_id_var.set(request_id)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["x-request-id"] = request_id
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    """What a load balancer polls, per docs/backend-architecture/00.md's
    availability section: confirms the process is actually serving
    requests, not just that it's running."""
    logger.info("health check ok")
    return {"status": "ok"}
