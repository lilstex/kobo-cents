import sentry_sdk
from celery import Celery
from celery.signals import setup_logging, task_prerun
from sentry_sdk.integrations.celery import CeleryIntegration

from app.core.config import settings
from app.core.logging import configure_logging, request_id_var

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[CeleryIntegration()],
        traces_sample_rate=0.1,
    )

celery_app = Celery("kobo_and_cents", broker=settings.redis_url, backend=settings.redis_url)


@setup_logging.connect
def _configure_worker_logging(**kwargs) -> None:
    configure_logging()


@task_prerun.connect
def _set_request_id_for_task(task_id: str, **kwargs) -> None:
    """Reuses the same contextvar the API's request-id middleware
    sets, so a worker's JSON log lines carry the task id the same way
    an API request's logs carry its request id, per
    docs/backend-architecture/03-phases.md's Sub-phase 0.3."""
    request_id_var.set(task_id)


# Task modules and the beat schedule (per-market refresh timing, per
# docs/backend-architecture/02.md) are Phase 3 work, not Phase 0. This
# app instance exists now so docker-compose can start a worker process.
