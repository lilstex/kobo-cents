import posthog

from app.core.config import settings

posthog.api_key = settings.posthog_api_key
posthog.host = settings.posthog_host
posthog.disabled = not settings.posthog_api_key


def track(event: str, user_id: str, properties: dict | None = None) -> None:
    """Every call in this codebase goes through here, never a direct
    posthog.capture(...), per docs/backend-architecture/00.md: keeps
    the analytics dependency swappable behind one function instead of
    scattered through the codebase. A no-op when POSTHOG_API_KEY isn't
    set, so development and tests never need real credentials."""
    posthog.capture(distinct_id=user_id, event=event, properties=properties or {})


def feature_flag_enabled(flag_key: str, user_id: str) -> bool:
    """The staged-rollout override app/services/entitlements.py's
    require_feature() checks alongside the subscriptions table, per
    docs/backend-architecture/02.md, the exact use case PostHog was
    chosen for in 00.md. False when PostHog isn't configured: a
    missing flag should never silently grant a paid feature for free."""
    if posthog.disabled:
        return False
    return bool(posthog.feature_enabled(flag_key, user_id))
