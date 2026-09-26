from app.integrations.market_data.base import ProviderNotConfiguredError
from app.workers.tasks.refresh_market_data import refresh_market_data_task
from app.workers.tasks.subscription_tasks import activate_subscription_task

# Sub-phase 10.2 of docs/backend-architecture/03-phases.md: "retry-
# with-backoff configured on every Celery task that calls an external
# provider (market data, payment webhooks)." Confirms the actual
# Celery task configuration took effect, not just that the decorator
# was written, per this project's own "verify real behavior" habit.


def test_refresh_market_data_task_retries_with_backoff_on_transient_errors():
    assert refresh_market_data_task.autoretry_for == (Exception,)
    assert refresh_market_data_task.retry_backoff is True
    assert refresh_market_data_task.max_retries == 3


def test_refresh_market_data_task_does_not_retry_a_permanent_config_error():
    # A missing API key fails identically on every retry; the next
    # scheduled cycle already covers it, an immediate retry storm
    # against it is pure waste, per the task's own reasoning.
    assert refresh_market_data_task.dont_autoretry_for == (ProviderNotConfiguredError,)


def test_activate_subscription_task_retries_with_backoff():
    assert activate_subscription_task.autoretry_for == (Exception,)
    assert activate_subscription_task.retry_backoff is True
    assert activate_subscription_task.max_retries == 5
