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
