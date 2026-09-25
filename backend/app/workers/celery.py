import sentry_sdk
from celery import Celery
from celery.schedules import crontab
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
# autodiscover_tasks's default related_name is "tasks", so passing the
# tasks package itself here ("app.workers.tasks") makes it look for a
# nonexistent app.workers.tasks.tasks submodule and silently register
# nothing. Passing the parent package makes it import app.workers.tasks
# (this package), whose __init__ imports the real task modules.
celery_app.autodiscover_tasks(["app.workers"])

# UTC throughout, per docs/backend-architecture/02.md's timezone
# reasoning, with each entry commented in the market's own local time
# rather than one blind global schedule. NGX runs WAT (UTC+1, no DST),
# so that offset is exact. US markets run ET (UTC-5 standard time,
# UTC-4 during US daylight saving), the times below use standard time;
# this does not auto-adjust for the DST transition twice a year, a
# known, named limitation, not an oversight, worth revisiting with a
# timezone-aware beat scheduler if the hour of drift twice a year ever
# turns out to matter in practice.
celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "refresh-ng-afternoon": {
        "task": "refresh_market_data",
        "schedule": crontab(hour=14, minute=0),  # 15:00 WAT, shortly after NGX's ~14:30 close
        "args": ("NG",),
    },
    "refresh-ng-evening": {
        "task": "refresh_market_data",
        "schedule": crontab(hour=19, minute=0),  # 20:00 WAT
        "args": ("NG",),
    },
    "refresh-us-afternoon": {
        "task": "refresh_market_data",
        "schedule": crontab(
            hour=21, minute=30
        ),  # 16:30 ET, shortly after the 16:00 NYSE/NASDAQ close
        "args": ("US",),
    },
    "refresh-us-evening": {
        "task": "refresh_market_data",
        "schedule": crontab(hour=1, minute=0),  # 20:00 ET
        "args": ("US",),
    },
}


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
