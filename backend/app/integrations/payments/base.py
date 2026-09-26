from dataclasses import dataclass
from typing import Protocol


class ProviderNotConfiguredError(Exception):
    """Raised loudly, never a silent no-op, per docs/backend-
    architecture/00.md: a payment provider failing quietly would be
    worse than a clear error, the same reasoning already applied to
    the market data providers."""


@dataclass
class CheckoutSession:
    redirect_url: str
    reference: str


@dataclass
class WebhookEvent:
    event_id: str
    event_type: str
    reference: str
    status: str  # "successful" | "other"


class PaymentProvider(Protocol):
    """One internal interface, a Paystack adapter and a Flutterwave
    adapter behind it, per docs/backend-architecture/00.md: adding,
    removing, or switching a provider is a new adapter, not a rewrite
    of subscription logic. Application code (app/api/v1/subscriptions.py,
    app/api/v1/webhooks.py) never imports either provider's SDK or API
    shape directly."""

    async def create_checkout(
        self, *, email: str, reference: str, amount: int, currency: str, callback_url: str
    ) -> CheckoutSession: ...

    def verify_webhook_signature(self, raw_body: bytes, headers: dict) -> bool: ...

    def parse_webhook_event(self, payload: dict) -> WebhookEvent: ...
