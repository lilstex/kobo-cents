import asyncio

from app.integrations.email.mailtrap import send_email
from app.workers.celery import celery_app


@celery_app.task(name="send_email_task", bind=True, max_retries=3, default_retry_delay=30)
def send_email_task(self, to: str, subject: str, html: str) -> None:
    """Sending an email never blocks the request that triggered it,
    per docs/backend-architecture/00.md. Retries with backoff on a
    transient Mailtrap failure rather than silently dropping the
    email or hammering a struggling provider immediately again."""
    try:
        asyncio.run(send_email(to, subject, html))
    except Exception as exc:
        raise self.retry(exc=exc) from exc
